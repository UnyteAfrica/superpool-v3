from django.contrib.auth import authenticate, get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import ScopedUserSerializer, UserAuthSerializer

User = get_user_model()


class SignUpView(APIView):
    @extend_schema(
        request=UserAuthSerializer,
        tags=["User"],
        operation_id="register",
        description="Create a new user with the provided data, and a new profile is created for the user.",
        responses={201: ScopedUserSerializer},
    )
    def post(self, request, data):
        serializer = UserAuthSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.create(**serializer.validated_data)
            return Response(
                {
                    "message": "User created successfully",
                    "user": UserAuthSerializer(user).data,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignInView(APIView):
    @extend_schema(
        request=UserAuthSerializer,
        tags=["User"],
        operation_id="login",
        description="Sign in to the application with the provided data. If the credentials are valid, a new access token will be generated.",
        responses={200: ScopedUserSerializer},
    )
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(email=email, password=password)

        if user:
            refresh = RefreshToken.for_user(user=user)
            return Response(
                {
                    "message": "User authenticated successfully",
                    "user": str(ScopedUserSerializer(user).data),
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )
