from core.claims.models import Claim
from django.core.exceptions import ValidationError
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.pagination import LimitOffsetPagination
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
        summary="View all claims made by your customers",
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
        ],
    )
    def list(self, request):
        """
        Retrieve a list of claims based on query parameters.
        """
        query_params = request.query_params.dict()
        service = self.get_service()
        try:
            claims = service.get_claims(query_params)

            # we want to, paginate the resulting queryset
            paginator = LimitOffsetPagination()
            page = paginator.paginate_queryset(claims, request)

            if page is not None:
                serializer = ClaimSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = ClaimSerializer(claims, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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

    @extend_schema(
        summary="Update the details of a previously filed claim by a cutstomer",
        parameters=[
            OpenApiParameter(
                name="claim_number",
                description="Claim Reference Number issued by the Insurance provider to help manage/track claim object",
            ),
        ],
        responses={200: ClaimSerializer},
    )
    def update(self, request, claim_number):
        """
        Endpoint to update an existing filed claim
        """
        serializer = ClaimWriteSerializer(data=request.data)

        data = serializer.validated_data
        if serializer.is_valid():
            service = self.get_service()
            # We want to retrive the claim instance then update it with the new details
            instance = service.get_claim(claim_number=data["claim_number"])

            if instance:
                claim = service.update_claim(
                    claim_number=data["claim_number"], data=data
                )
                response_serializer = ClaimSerializer(claim)
                return Response(
                    {
                        "data": response_serializer.data,
                        "message": "Claim updated successfully",
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {
                    "error": "It seems we fcked up! Please contact support for swift resolution!",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)