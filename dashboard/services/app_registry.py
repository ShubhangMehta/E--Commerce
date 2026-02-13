TENANT_APPS = [
    {
    'key': 'users',
    'name': 'Customers',
    'url_name': 'users:list',   # adjust to your urls
    'description': 'Manage users and roles',
    'icon': 'users',
    },
    {
    'key': 'orders',
    'name': 'Orders',
    'url_name': 'orders:dashboard_order_list',
    'description': 'View and manage customer orders',
    'icon': 'shopping-cart',
    },
    {
    'key': 'catalog',
    'name': 'catalog',
    'url_name': 'catalog:product_list',
    'description': 'Manage product catalog',
    'icon': 'grid',
    },
#{
#    'key': 'inventory',
#    'name': 'Inventory',
#    'url_name': 'inventory:list',
#    'description': 'Track stock and availability',
#    'icon': 'archive',
#},
#{
#    'key': 'themes',
#    'name': 'Themes',
#    'url_name': 'themes:list',
#    'description': 'Customize store appearance',
#    'icon': 'palette',
#},
]
