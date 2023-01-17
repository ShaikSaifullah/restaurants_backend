from app import application
from flask import jsonify, Response, session
from app.models import *
from app import *
import uuid
import datetime
from marshmallow import Schema, fields
from flask_restful import Resource, Api
from flask_apispec.views import MethodResource
from flask_apispec import marshal_with, doc, use_kwargs
import json


class SignUpRequest(Schema):
    name = fields.Str(default="name")
    username = fields.Str(default="username")
    password = fields.Str(default="password")
    level = fields.Int(default=0)


class LoginRequest(Schema):
    username = fields.Str(default="username")
    password = fields.Str(default="password")


class AddVendorRequest(Schema):
    user_id = fields.Str(default="user_id")


class AddItemRequest(Schema):
    item_name = fields.Str(default="item_name")
    calories_per_gm = fields.Int(default=0)
    available_quantity = fields.Int(default=0)
    restaurant_name = fields.Str(default="restaurant_name")
    unit_price = fields.Int(default=0)


class OrderItemsRequest(Schema):
    items = fields.Dict(fields.Str(default="item_id"), fields.Int(default=0))


class PlaceOrderRequest(Schema):
    order_id = fields.Str(default="order_id")


class APIResponse(Schema):
    message = fields.Str()
    error = fields.Str()


class VendorsListResponse(Schema):
    vendors = fields.List(fields.Dict())
    error = fields.Str()


class ItemsListResponse(Schema):
    items = fields.List(fields.Dict())
    error = fields.Str()


class OrdersListResponse(Schema):
    orders = fields.List(fields.Dict())
    error = fields.Str()


#  Restful way of creating APIs through Flask Restful
class SignUpAPI(MethodResource, Resource):
    @doc(description='Sign Up API', tags=['SignUp API'])
    @use_kwargs(SignUpRequest, location=('json'))
    @marshal_with(APIResponse)
    def post(self, **kwargs):
        try:
            user = User(
                user_id=uuid.uuid4(),
                name=kwargs['name'],
                username=kwargs['username'],
                password=kwargs['password'],
                level=kwargs['level']
            )
            db.session.add(user)
            db.session.commit()
            return APIResponse().dump(dict(message='User successfully registered')), 200
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(error=f'Not able to register: {str(e)}')), 400


api.add_resource(SignUpAPI, '/signup')
docs.register(SignUpAPI)


class LoginAPI(MethodResource, Resource):
    @doc(description='Login API', tags=['Login API'])
    @use_kwargs(LoginRequest, location=('json'))
    @marshal_with(APIResponse)
    def post(self, **kwargs):
        try:
            user = User.query.filter_by(username=kwargs['username'], password=kwargs['password']).first()
            if user:
                print(f'Logged In as {kwargs["username"]}')
                session['user_id'] = user.user_id
                #print(f'User ID: {str(session["user_id"])}')
                return APIResponse().dump(dict(message='User logged in successfully')), 200
            else:
                return APIResponse().dump(dict(error='No User with given credentials Found')), 404
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(error=f'Login Failed: {str(e)}')), 400


api.add_resource(LoginAPI, '/login')
docs.register(LoginAPI)


class LogoutAPI(MethodResource, Resource):
    @doc(description='Logout API', tags=['Logout API'])
    @marshal_with(APIResponse)
    def post(self, **kwargs):
        try:
            if session['user_id']:
                session['user_id'] = None
                print('Logged out')
                return APIResponse().dump(dict(message='User logged out successfully')), 200
            else:
                return APIResponse().dump(dict(error='User not logged in')), 401
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(error=f'Logout failed: {str(e)}')), 400
            

api.add_resource(LogoutAPI, '/logout')
docs.register(LogoutAPI)


class AddVendorAPI(MethodResource, Resource):
    @doc(description='Add Vendor API', tags=['Add Vendor API'])
    @use_kwargs(AddVendorRequest, location=('json'))
    @marshal_with(APIResponse)
    def post(self, **kwargs):
        try:
            user = User.query.filter_by(user_id= kwargs['user_id']).first()
            user.level = 1
            user.updated_ts = datetime.datetime.utcnow()
            db.session.commit()
            print("User Updated to Vendor")
            return APIResponse().dump(dict(message=f'{user.name} updated to Vendor Successfully')), 200
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(error=f'Updating to Vendor Failed: {str(e)}')), 400
            

api.add_resource(AddVendorAPI, '/add_vendor')
docs.register(AddVendorAPI)


class GetVendorsAPI(MethodResource, Resource):
    @doc(description='Get Vendors API', tags=['Get Vendors API'])
    @marshal_with(VendorsListResponse)
    def get(self):
        try:
            if session['user_id']:
                vendors = User.query.filter_by(level=1)
                vendorsList = list()
                for vendor in vendors:
                    vendor_dict = {}
                    vendor_dict['user_id'] = vendor.user_id
                    vendor_dict['name'] = vendor.name
                    vendor_dict['is_active'] = 'Active' if vendor.is_active == 1 else 'Inactive'
                    items = Item.query.filter_by(vendor_id=vendor.user_id)
                    avl_items = list()
                    restaurant = ''
                    for item in items:
                        avl_items.append(item.item_name)
                        restaurant = item.restaurant_name
                    vendor_dict['items'] = avl_items
                    vendor_dict['restaurant'] = restaurant

                    vendorsList.append(vendor_dict)
                #print(vendorsList)
                return VendorsListResponse().dump(dict(vendors=vendorsList)), 200
            else:
                print("User not Logged in")
                return VendorsListResponse().dump(dict(error='User not Logged In')), 401
        except Exception as e:
            print(str(e))
            return VendorsListResponse().dump(dict(error=f'Fetching Vendors Failed: {str(e)}')), 400


api.add_resource(GetVendorsAPI, '/list_vendors')
docs.register(GetVendorsAPI)


class AddItemAPI(MethodResource, Resource):
    @doc(description='Add Items API', tags=['Add Items API'])
    @use_kwargs(AddItemRequest, location=('json'))
    @marshal_with(APIResponse)
    def post(self, **kwargs):
        try:
            if session['user_id']:
                user = User.query.filter_by(user_id=session['user_id']).first()
                if user.level == 1:
                    item = Item(
                        item_id=uuid.uuid4(),
                        vendor_id=user.user_id,
                        item_name=kwargs['item_name'],
                        calories_per_gm=kwargs['calories_per_gm'],
                        available_quantity=kwargs['available_quantity'],
                        restaurant_name=kwargs['restaurant_name'],
                        unit_price=kwargs['unit_price']
                    )
                    db.session.add(item)
                    db.session.commit()
                    return APIResponse().dump(dict(message='Item added Successfully')), 200
                else:
                    print("Only Vendors are allowed to add Items")
                    return APIResponse().dump(dict(error='Not Authorized')), 401
            else:
                print("Not Logged In")
                return APIResponse().dump(dict(error='Not Logged In')), 401
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(error=f'Failed adding Item: {str(e)}')), 400


api.add_resource(AddItemAPI, '/add_item')
docs.register(AddItemAPI)


class ListItemsAPI(MethodResource, Resource):
    @doc(description='List Items API', tags=['List Items API'])
    @marshal_with(ItemsListResponse)
    def get(self):
        try:
            items = Item.query.all()
            items_list = list()
            for item in items:
                item_dict = {}
                item_dict['item_id'] = item.item_id
                item_dict['item_name'] = item.item_name
                item_dict['vendor_id'] = item.vendor_id
                item_dict['available_quantity'] = item.available_quantity
                item_dict['is_active'] = item.is_active
                item_dict['restaurant_name'] = item.restaurant_name
                item_dict['unit_price'] = item.unit_price

                items_list.append(item_dict)
            #print(items_list)
            return ItemsListResponse().dump(dict(items=items_list)), 200
        except Exception as e:
            print(str(e))
            return ItemsListResponse().dump(dict(error=f'Could not fetch {str(e)}')), 400


api.add_resource(ListItemsAPI, '/list_items')
docs.register(ListItemsAPI)


#While adding items and quantity add it as dict {"item_id"'s : quantity's}
class CreateItemOrderAPI(MethodResource, Resource):
    @doc(description='Create Item Order API', tags=['Create Item Order API'])
    @use_kwargs(OrderItemsRequest, location=('json'))
    @marshal_with(APIResponse)
    def post(self, **kwargs):
        try:
            if session['user_id']:
                items = kwargs['items']
                print(items)
                total_value = 0
                order = Order(
                    order_id=uuid.uuid4(),
                    user_id=session['user_id']
                )
                db.session.add(order)
                for idItem in items:
                    item = Item.query.filter_by(item_id=idItem).first()
                    if items[idItem] <= item.available_quantity:
                        total_value += item.unit_price * items[idItem]
                        orderItem = OrderItems(
                            id=uuid.uuid4(),
                            order_id=order.order_id,
                            item_id=idItem,
                            quantity=items[idItem]
                        )
                        db.session.add(orderItem)
                    else:
                        return APIResponse().dump(dict(error=f'Failed creating order. Available quantity of {item.item_name} is only {str(item.available_quantity)}')), 401
                order.total_amount = total_value
                db.session.commit()
                return APIResponse().dump(dict(message='Successfully added items and Quantities')), 200
            else:
                return APIResponse().dump(dict(error='Not Logged In')), 401
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(error=f'Failed to add Items to Order: {str(e)}')), 400


api.add_resource(CreateItemOrderAPI, '/create_items_order')
docs.register(CreateItemOrderAPI)


class PlaceOrderAPI(MethodResource, Resource):
    @doc(description='Place Order API', tags=['Place Order API'])
    @use_kwargs(PlaceOrderRequest, location=('json'))
    @marshal_with(APIResponse)
    def put(self, **kwargs):
        try:
            if session['user_id']:
                order = Order.query.filter_by(order_id=kwargs['order_id']).first()
                if order.is_placed != 1:
                    if order.user_id == session['user_id']:
                        order.is_placed = 1
                        order.updated_ts = datetime.datetime.utcnow()

                        orderItem = OrderItems.query.filter_by(order_id=kwargs['order_id'])
                        for oi in orderItem:
                            item = Item.query.filter_by(item_id=oi.item_id).first()
                            item.available_quantity = item.available_quantity - oi.quantity
                            item.updated_ts = datetime.datetime.utcnow()

                        db.session.commit()
                        return APIResponse().dump(dict(message='Order placed Successfully')), 200
                    else:
                        return APIResponse().dump(dict(error='Order belongs to other user')), 400
                else:
                    return APIResponse().dump(dict(message='Order already placed Successfully')), 400
            else:
                print('Not Logged in')
                return APIResponse().dump(dict(error='Not logged in')), 401
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(error=f'Failed to Place Order: {str(e)}')), 400


api.add_resource(PlaceOrderAPI, '/place_order')
docs.register(PlaceOrderAPI)


class ListOrdersByCustomerAPI(MethodResource, Resource):
    @doc(description='List Orders by Customer API', tags=['List Orders by Customer API'])
    @marshal_with(OrdersListResponse)
    def get(self):
        try:
            if session['user_id']:
                orders = Order.query.filter_by(user_id=session['user_id'])
                orders_list = list()
                for order in orders:
                    order_dict = {}
                    order_dict['order_id'] = order.order_id
                    order_dict['total_amount'] = order.total_amount
                    order_dict['created_ts'] = order.created_ts
                    order_dict['updated_ts'] = order.updated_ts
                    order_dict['status'] = 'Placed' if order.is_placed == 1 else 'Not Placed'

                    orders_list.append(order_dict)
                #print(orders_list)
                return OrdersListResponse().dump(dict(orders=orders_list)), 200
            else:
                return OrdersListResponse().dump(dict(error='Not logged In')), 401
        except Exception as e:
            print(str(e))
            return OrdersListResponse().dump(dict(error=f'Failed to fetch: {str(e)}')), 400


api.add_resource(ListOrdersByCustomerAPI, '/list_orders')
docs.register(ListOrdersByCustomerAPI)


class ListAllOrdersAPI(MethodResource, Resource):
    @doc(description='List All Orders', tags=['List ALL Orders'])
    @marshal_with(OrdersListResponse)
    def get(self):
        try:
            if session['user_id']:
                user = User.query.filter_by(user_id=session['user_id']).first()
                if user.level == 2:
                    orders = Order.query.all()
                    orders_list = list()
                    for order in orders:
                        order_dict = {}
                        order_dict['order_id'] = order.order_id
                        order_dict['total_amount'] = order.total_amount
                        order_dict['created_ts'] = order.created_ts
                        order_dict['updated_ts'] = order.updated_ts
                        order_dict['status'] = 'Placed' if order.is_placed == 1 else 'Not Placed'

                        orders_list.append(order_dict)
                    #print(orders_list)
                    return OrdersListResponse().dump(dict(orders=orders_list)), 200
                else:
                    print('Only Admins have this access')
                    return OrdersListResponse().dump(dict(error='Not Authorised - Admins Only')), 401
            else:
                return OrdersListResponse().dump(dict(error='Not logged In'))
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(error=f'Failed to fetch: {str(e)}')), 400


api.add_resource(ListAllOrdersAPI, '/list_all_orders')
docs.register(ListAllOrdersAPI)