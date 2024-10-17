from decimal import Decimal

from django.test import TestCase

from api.catalog.serializers import AutoInsuranceSerializer


class AutoInsuranceSerializerTest(TestCase):
    def test_valid_auto_insurance(self):
        data = {
            "vehicle_type": "Car",
            "vehicle_make": "Mercedes Benz",
            "vehicle_model": "S Class",
            "vehicle_year": 2021,
            "vehicle_value": 10000000,
            "vehicle_usage": "Private",
            "insurance_type": "Comprehensive",
        }

        serializer = AutoInsuranceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["product_id"], 823)

    def test_missing_required_fields_for_car(self):
        # Missing: 'vehicle_make', 'vehicle_value', 'vehicle_usage', 'vehicle_year'
        data = {
            "vehicle_type": "Car",
        }

        serializer = AutoInsuranceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("vehicle_make", serializer.errors)
        self.assertIn("vehicle_value", serializer.errors)
        self.assertIn("vehicle_usage", serializer.errors)
        self.assertIn("vehicle_year", serializer.errors)

    def test_invalid_insurance_type(self):
        data = {
            "vehicle_type": "Car",
            "vehicle_make": "Mercedes Benz",
            "vehicle_model": "S Class",
            "vehicle_year": 2021,
            "vehicle_value": Decimal("10000000"),
            "vehicle_usage": "Private",
            "insurance_type": "Invalid Insurance Type",
        }

        serializer = AutoInsuranceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("insurance_type", serializer.errors)
        self.assertEqual(
            serializer.errors["insurance_type"][0],
            "Invalid insurance type: Invalid Insurance Type",
        )

    def test_invalid_insurance_type_for_bike(self):
        data = {
            "vehicle_type": "Bike",
            "vehicle_make": "Yamaha",
            "vehicle_model": "R1",
            "vehicle_year": 2021,
            "vehicle_value": Decimal("500000"),
            "vehicle_usage": "Private",
            "insurance_type": "Invalid Type",
        }

        serializer = AutoInsuranceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("insurance_type", serializer.errors)
        self.assertEqual(
            serializer.errors["insurance_type"][0],
            "Invalid insurance type: Invalid Type",
        )

    def test_valid_auto_insurance_for_bike(self):
        data = {
            "vehicle_type": "Bike",
            "vehicle_make": "Yamaha",
            "vehicle_model": "R1",
            "vehicle_year": 2021,
            "vehicle_value": 500000,
            "vehicle_usage": "Private",
            "insurance_type": "Third Party",
        }

        serializer = AutoInsuranceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["product_id"], 821)
