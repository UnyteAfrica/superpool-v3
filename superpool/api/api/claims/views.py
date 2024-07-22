from core.claims.models import Claim
from django.core.exceptions import ValidationError
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response

from .exceptions import NotFound
from .serializers import ClaimSerializer, ClaimWriteSerializer
from .services import ClaimService


class ClaimsViewSet(viewsets.ViewSet):
    def get_service(self):
        """
        Returns the instance of our Claims Service
        """
        return ClaimService()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="customer_email",
                required=False,
                type=OpenApiTypes.EMAIL,
            ),
            OpenApiParameter(
                name="first_name",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="last_name",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="phone_number",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="claim_type",
                description="",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="claim_owner",
                description="",
                required=False,
                type=OpenApiTypes.STR,
            ),
        ]
    )
    def list(self, request):
        pass

    @extend_schema(
        summary="Retrieve a claim by its ID or Reference Number",
        parameters=[
            OpenApiParameter("claim_number"),
            OpenApiParameter("claim_id"),
        ],
        responses={200: ClaimSerializer},
    )
    def retrieve(self, request, claim_number=None, pk=None):
        """
        Retrieve a single claim by its unique ID or claim reference number
        """
        service = self.get_service()
        try:
            claim = service.get_claim(claim_number=claim_number, claim_id=pk)
            serializer = ClaimSerializer(claim)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Claim.DoesNotExist:
            raise NotFound("Claim not found")
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id="submit_claim",
        summary="Submit a claim",
        description="Submits a new claim entry on behalf of a customer",
        responses={
            200: ClaimSerializer,
        },
    )
    def create(self, request, *args, **kwargs):
        """
        Endpoint to submit a new claim
        """
        serializer = ClaimWriteSerializer(data=request.data)
        if serializer.is_valid():
            try:
                service = self.get_service()
                claim = service.submit_claim(serializer.validated_data)
                response_serializer = ClaimSerializer(claim)
                return Response(
                    {
                        "data": response_serializer.data,
                        "message": "Claim successfully submitted",
                    },
                    status=status.HTTP_201_CREATED,
                )
            except ValidationError as err:
                return (
                    Response({"error": str(err)}, status=status.HTTP_400_BAD_REQUEST),
                )
            except Exception as exc:
                return (
                    Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST),
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
