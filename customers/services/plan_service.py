# # customers/services/plan_service.py

# def activate_plan(client, plan):
#     """
#     Called ONLY after successful payment
#     """

#     if plan.code == "SINGLE_PLAN":
#         client.product_mode = "single"

#     elif plan.code == "MULTI_PLAN":
#         client.product_mode = "multi"

#     client.is_active = True
#     client.save()


def activate_plan(client, plan):
    """
    Called ONLY after successful payment
    """

    if plan.name == "basic":        # single product
        client.product_mode = "single"

    elif plan.name in ["standard", "premium"]:
        client.product_mode = "multi"

    client.save(update_fields=["product_mode"])
