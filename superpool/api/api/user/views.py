import logging
from django.contrib.auth import authenticate, get_user_model, login
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiRequest,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.serializers import ValidationError
from django.db import IntegrityError
from core.user.models import CustomerSupport, Admin
from core.merchants.models import Merchant
from api.user.serializers import CustomerSupportSerializer, AdminSerializer

from .serializers import (
    MerchantAuthSerializer,
    ScopedUserSerializer,
    UserAuthSerializer,
    UserSerializer,
)

User = get_user_model()

logger = logging.getLogger(__name__)


class SignUpView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        request=OpenApiRequest(
            request=UserSerializer,
            examples=[
                OpenApiExample(
                    "Customer Support Registration",
                    description="The data required to create a new user.",
                    value={
                        "email": "rasengan@email.com",
                        "first_name": "Naruto",
                        "last_name": "Uzumaki",
                        "password": "password",
                        "role": "support",
                    },
                ),
                OpenApiExample(
                    "Admin Registration",
                    description="The data required to create a new user.",
                    value={
                        "email": "tsunadesama@email.com",
                        "first_name": "Tsunade",
                        "last_name": "Senju",
                        "password": "password",
                        "role": "admin",
                    },
                ),
            ],
        ),
        operation_id="register",
        summary="Create a new user - Admin or Customer Support",
        description="Create a new user with the provided data, and a new profile is created for the user.",
        responses={
            201: OpenApiResponse(
                response=ScopedUserSerializer,
                description="User created successfully",
                examples=[
                    OpenApiExample(
                        "User Registration",
                        description="The user profile for the newly created user.",
                        value={
                            "status": "success",
                            "message": "User created successfully",
                            "data": {
                                "first_name": "Naruto",
                                "last_name": "Uzumaki",
                                "email": "naruto@hokage.com",
                                "role": "support",
                                "admin_profile": "null",
                                "support_profile": {
                                    "is_staff": True,
                                },
                            },
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Validation error",
                examples=[
                    OpenApiExample(
                        "Validation Error",
                        description="The error message for the validation error.",
                        value={"message": "Validation error: <error message>"},
                    )
                ],
            ),
            500: OpenApiResponse(
                description="An error occurred",
                examples=[
                    OpenApiExample(
                        "Error",
                        description="The error message for the internal server error.",
                        value={
                            "message": "An error occurred",
                            "error": "<error message>",
                        },
                    )
                ],
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            print(f"Validated data: {serializer.validated_data}")
            try:
                user = serializer.save()
                user_profile_serializer = ScopedUserSerializer(user)
                return Response(
                    {
                        "status": "success",
                        "message": "User created successfully",
                        "data": user_profile_serializer.data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except IntegrityError as e:
                return Response(
                    {"message": "Integrity error: " + str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except ValidationError as e:
                return Response(
                    {"message": "Validation error: " + str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                logger.error(f"Error creating user: {str(e)}")
                return Response(
                    {"message": "An error occurred", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignInView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=OpenApiRequest(
            request=UserAuthSerializer,
        ),
        tags=["Auth"],
        operation_id="login",
        summary="Authenticate as an internal user - Admin or Customer Support",
        description="Sign in to the application with the provided data. If the credentials are valid, a new access token will be generated.",
        responses={200: ScopedUserSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = UserAuthSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            user = authenticate(request, email=email, password=password)

            if user:
                login(request, user)

                return Response(
                    {
                        "message": "Logged in successfully",
                        "data": ScopedUserSerializer(user).data,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MerchantLoginView(APIView):
    """
    Handles Merchant login via Tenant ID and Password
    """

    @extend_schema(
        tags=["Auth"],
        request=OpenApiRequest(
            request=MerchantAuthSerializer,
        ),
        operation_id="merchant_login",
        summary="Logon to superpool dashboard as a merchant",
        description="Authenticate a merchant using their tenant ID and password.",
        responses={
            200: OpenApiResponse(
                description="Merchant authenticated successfully",
                examples=[
                    OpenApiExample(
                        "Merchant Login",
                        description="The data for the authenticated merchant.",
                        value={
                            "merchant_id": 1,
                            "merchant_name": "Merchant Name",
                            "refresh": "<refresh-token>",
                            "access": "<access-token>",
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Validation error",
                examples=[
                    OpenApiExample(
                        "Validation Error",
                        description="The error message for the validation error.",
                        value={"message": "Validation error: <error message>"},
                    )
                ],
            ),
            401: OpenApiResponse(
                description="Invalid credentials",
                examples=[
                    OpenApiExample(
                        "Invalid Credentials",
                        description="The error message for invalid credentials.",
                        value={"message": "Invalid credentials"},
                    )
                ],
            ),
            404: OpenApiResponse(
                description="Merchant not found",
                examples=[
                    OpenApiExample(
                        "Merchant not found",
                        description="The error message for merchant not found.",
                        value={"message": "Merchant not found"},
                    )
                ],
            ),
            500: OpenApiResponse(
                description="An error occurred",
                examples=[
                    OpenApiExample(
                        "Error",
                        description="The error message for the internal server error.",
                        value={
                            "message": "An error occurred",
                            "error": "<error message>",
                        },
                    )
                ],
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = MerchantAuthSerializer(data=request.data)

        if serializer.is_valid():
            tenant_id = serializer.validated_data["tenant_id"]
            password = serializer.validated_data["password"]

            try:
                merchant = Merchant.objects.filter(tenant_id=tenant_id).first()
            except Merchant.DoesNotExist:
                return Response(
                    {"error": "Merchant not found."}, status=status.HTTP_404_NOT_FOUND
                )

            # Authenticate using the merchant's associated user account
            merchant_email = merchant.business_email
            user = authenticate(request, username=merchant_email, password=password)

            if user is not None:
                refresh = RefreshToken.for_user(user)
                return Response(
                    {
                        "merchant_id": merchant.id,
                        "merchant_name": merchant.name,
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    }
                )
            else:
                return Response(
                    {"error": "Invalid credentials."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        # serializer is invalid
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
