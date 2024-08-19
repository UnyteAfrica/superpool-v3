from abc import abstractmethod, ABC
from decimal import Decimal


PRICING_DATA = {
    "Smart Motorist Protection Plan": {
        "Basic": {
            "premium": Decimal("2000.00"),
            "flat_fee": True,
            "commission_percent": Decimal("20"),
        },
        "Standard": {
            "premium": Decimal("3500.00"),
            "flat_fee": True,
            "commission_percent": Decimal("20"),
        },
        "Premium": {
            "premium": Decimal("5500.00"),
            "flat_fee": True,
            "commission_percent": Decimal("20"),
        },
    },
    "Smart Traveler Protection Plan": {
        "Bronze": {
            "premium": Decimal("2000.00"),
            "flat_fee": True,
            "commission_percent": Decimal("20"),
        },
        "Silver": {
            "premium": Decimal("3000.00"),
            "flat_fee": True,
            "commission_percent": Decimal("20"),
        },
        "Gold": {
            "premium": Decimal("1500.00"),
            "flat_fee": True,
            "commission_percent": Decimal("20"),
        },
    },
    "Smart Generations Protection": {
        "Bronze": {
            "premium": Decimal("2500.00"),
            "flat_fee": True,
            "commission_percent": Decimal("20"),
        },
        "Silver": {
            "premium": Decimal("3500.00"),
            "flat_fee": True,
            "commission_percent": Decimal("20"),
        },
        "Gold": {
            "premium": Decimal("5000.00"),
            "flat_fee": True,
            "commission_percent": Decimal("20"),
        },
    },
    "Home Protection Policy": {
        "Bronze": {
            "premium": Decimal("1500.00"),
            "flat_fee": True,
            "commission_percent": Decimal("20"),
        },
        "Silver": {
            "premium": Decimal("2500.00"),
            "flat_fee": True,
            "commission_percent": Decimal("20"),
        },
        "Gold": {
            "premium": Decimal("3500.00"),
            "flat_fee": True,
            "commission_percent": Decimal("20"),
        },
        "Platinum": {
            "premium": Decimal("5000.00"),
            "flat_fee": True,
            "commission_percent": Decimal("20"),
        },
    },
    "Personal Accident": {
        "Basic": {
            "premium": Decimal("1250.00"),
            "flat_fee": True,
            "commission_percent": Decimal("10"),
        },
        "Silver": {
            "premium": Decimal("2450.00"),
            "flat_fee": True,
            "commission_percent": Decimal("10"),
        },
    },
    "Student Protection Plan": {
        "Annual": {
            "premium": Decimal("12000.00"),
            "flat_fee": True,
            "commission_percent": Decimal("10"),
        },
        "Monthly": {
            "premium": Decimal("1000.00"),
            "flat_fee": True,
            "commission_percent": Decimal("10"),
        },
    },
    "Auto Insurance": {
        "Autobase": {
            "premium": Decimal("30000.00"),
            "flat_fee": True,
            "commission_percent": Decimal("12.50"),
        },
        "Third-Party": {
            "premium": Decimal("15000.00"),
            "flat_fee": True,
            "commission_percent": Decimal("12.50"),
        },
    },
}
""" Pricing data for insurance products """


class RiskAssessmentEngine(ABC):
    @abstractmethod
    def assess_risk(self, insurance_details: dict) -> tuple[int, Decimal]:
        """
        Assess risk based on insurance details and return a risk score,
        the higher the score the higher the risk.

        It also returns a decimal value representing the additional cost due to risk
        """
        pass

    @abstractmethod
    def get_risk_score(self, customer_id: str) -> int:
        """
        Get the risk score for a customer
        """
        pass

    @abstractmethod
    def calulate_risk_score(self, customer_id: str) -> int:
        """
        Calculate the risk score for a customer
        """
        pass

    @abstractmethod
    def calculate_risk_cost(self, risk_score: int) -> Decimal:
        """
        Calculate the additional cost due to risk
        """
        pass

    def calulate_base_price(
        self, product_type: str, coverage_type: str, insurance_name: str
    ) -> Decimal:
        """
        Calculate the base price for a product type
        """
        if insurance_name in PRICING_DATA:
            coverage = PRICING_DATA[insurance_name].get(coverage_type)
            if coverage:
                return coverage["premium"]
        return Decimal(0)

    def calculate_discount(self, discount: int) -> Decimal:
        """
        Calculate the discount for a customer
        """
        pass

    def calulate_quote(
        self, product_type: str, insurance_details: dict, customer_id: str
    ) -> Decimal:
        """
        Calculate the quote for a customer
        """
        insurance_name = insurance_details.get("insurance_name")
        coverage_type = insurance_details.get("coverage_type", "Basic")
        base_price = self.calculate_base_price(
            product_type, insurance_name, coverage_type
        )
        risk_score, risk_cost = self.assess_risk(insurance_details)
        risk_cost = self.calculate_risk_cost(risk_score)
        discount = self.calculate_discount(customer_id)
        quote = base_price + risk_cost - discount
        return quote


class TravelInsuranceEngine(RiskAssessmentEngine):
    def assess_risk(self, insurance_details: dict) -> tuple[int, Decimal]:
        """
        Assess risk for travel insurance based on destination, trip duration, etc.
        """

        # The Algorithm:
        #
        # the algorithm uses a weighted ranking system to calculate the risk score
        # the longer the trip duration does not have effect on risk score (if within 30 days),
        # the destination has a higher impact on the risk score.
        #
        # other factors like number of dependents/travellers, etc. impacts the risk score
        WEIGHTED_SCORE = 0.1
        risk_score = 0
        risk_cost = Decimal(0)

        CONTINENTS = ["Europe", "North America", "Oceania", "Asia", "South America"]

        WHITELISTED_DESTINATIONS = [
            "USA",
            "UK",
            "Germany",
            "France",
            "Spain",
            "Italy",
            "Japan",
            "Australia",
            "Greece",
            "Canada",
            "Brazil",
        ]
        BLACKLISTED_DESTINATIONS = ["Syria", "Iraq", "Iran"]

        destination = insurance_details.get("destination")

        if destination in BLACKLISTED_DESTINATIONS:
            # High risk
            pass

        # destination not in blacklisted destinations
        if destination in WHITELISTED_DESTINATIONS or destination in CONTINENTS:
            # Low risk
            pass

        return risk_score, risk_cost


class HealthInsuranceEngine(RiskAssessmentEngine):
    def assess_risk(self, insurance_details: dict) -> tuple[int, Decimal]:
        """
        Assess risk for health insurance based on pre-existing conditions, behavioural data,
        personal information such as age, etc.
        """

        HEALTHY_LIFESTYLE = ["Non-smoker", "Non-drinker", "Regular exercise"]
        HEALTH_CONDITION_TYPE = ["Diabetes", "Hypertension", "Cancer", "Asthma"]
        HEALTH_CONDITION = ["Good", "Fair", "Poor", "Critical"]

        # people above 60 years are considered high risk, as they are more likely to have health conditions
        HIGH_RISK_AGE = 60
        risk_score = 0
        risk_cost = Decimal(0)

        age = insurance_details.get("age")
        health_condition = insurance_details.get("health_condition")

        if age > HIGH_RISK_AGE:
            risk_score += 20
            risk_cost += Decimal("500.00")

        if (
            health_condition in HEALTH_CONDITION_TYPE
            and health_condition in HEALTH_CONDITION
        ):
            risk_score += 10
            risk_cost += Decimal("200.00")

        return risk_score, risk_cost


class HomeInsuranceEngine(RiskAssessmentEngine):
    def assess_risk(self, insurance_details: dict) -> tuple[int, Decimal]:
        """
        Assess risk for home insurance based on location, building type, etc.
        """
        home_age = insurance_details.get("home_age", 0)
        home_value = insurance_details.get("home_value", 0)
        risk_score = 0
        risk_cost = Decimal("0.00")

        # any home greater than 20 years old has a higher risk score
        if home_age > 20:
            risk_score += 10
            risk_cost += Decimal("150.00")
        # home valued at 25 Million naira or more has a higher risk score
        if home_value > 1000000:
            risk_score += 20
            risk_cost += Decimal("300.00")

        return risk_score, risk_cost

    def calculate_risk_cost(self, risk_score: int) -> Decimal:
        """
        Calculate the additional cost due to risk
        """
        pass
