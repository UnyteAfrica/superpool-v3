from django.contrib.auth import authenticate, get_user_model, login
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import ScopedUserSerializer, UserAuthSerializer, UserSerializer

User = get_user_model()


class SignUpView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=UserAuthSerializer,
        tags=["User"],
        operation_id="register",
        description="Create a new user with the provided data, and a new profile is created for the user.",
        responses={201: ScopedUserSerializer},
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.create(**serializer.validated_data)
            refresh_token = RefreshToken.for_user(user=user)
            return Response(
                {
                    "message": "User created successfully",
                    "user": UserAuthSerializer(user).data,
                    "refresh": str(refresh_token),
                    "access": str(refresh_token.access_token),
                },
                status=status.HTTP_201_CREATED,
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
