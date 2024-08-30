import dataclasses

from django.db.models import Model


@dataclasses.dataclass
class ActionType(object):
    """
    Event registered to perform an operation on a model.
    """

    name: str

    def register(self, model: Model, **kwargs):
        """
        Register the event with the model.
        """
        return NotImplementedError()


class CreateMerchantAction(ActionType):
    """
    Create a new merchant.
    """

    name = "create_merchant"


class UpdateMerchantAction(ActionType):
    """
    Update an existing merchant.
    """

    name = "update_merchant"


class DeactivateMerchantAction(ActionType):
    """
    Deactivate an existing merchant.
    """

    name = "deactivate_merchant"


class ActivateMerchantAction(ActionType):
    """
    Activate an merchant account
    """

    name = "activate_merchant"
