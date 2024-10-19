from core.user.models import Customer


class CustomerService:
    """
    Defines a set of consistent actions as interfaces that can be performed
    on the customer apis
    """

    @staticmethod
    def list_all_customers():
        return Customer.objects.all()

    @staticmethod
    def list_customers_by_merchant(merchant):
        return Customer.objects.filter(merchant=merchant)

    @staticmethod
    def get_customer_policies(customer):
        return customer.policies.all()

    @staticmethod
    def get_active_policies(customer):
        return customer.policies.filter(status="active")

    @staticmethod
    def get_active_claims(customer):
        return customer.claims.filter(status="active")
