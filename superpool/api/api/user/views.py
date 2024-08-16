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

from .serializers import ScopedUserSerializer, UserAuthSerializer, UserSerializer

User = get_user_model()


class SignUpView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=OpenApiRequest(
            UserSerializer,
            examples=[
                OpenApiExample(
                    "User Registration",
                    description="The data required to create a new user.",
                    value={
                        "email": "rasengan@email.com",
                        "first_name": "Naruto",
                        "last_name": "Uzumaki",
                        "password": "password",
                        "role": "customer",
                    },
                )
            ],
        ),
        tags=["User"],
        operation_id="register",
        description="Create a new user with the provided data, and a new profile is created for the user.",
        responses={201: OpenApiResponse(response=ScopedUserSerializer)},
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                return Response(
                    {
                        "status": "success",
                        "message": "User created successfully",
                        "data": ScopedUserSerializer(user).data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except (IntegrityError, ValidationError) as e:
                return Response(
                    {"message": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                return Response(
                    {"message": "An error occurred", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignInView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=UserAuthSerializer,
        tags=["User"],
        operation_id="login",
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
