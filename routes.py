from categories import Categories

def route_function(request_data,path):
    match path:
        case '/create_category':
            return Categories.create_category(request_data)
        case '/delete_category':
            return Categories.delete_category(request_data)
        case '/edit_category':
            return Categories.edit_category(request_data)
        case '/get_category':
            return Categories.get_category(request_data)
        case '/get_all_categories_for_department':
            return Categories.get_all_categories_for_department(request_data)