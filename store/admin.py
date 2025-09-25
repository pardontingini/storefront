from django.contrib import admin, messages
from django.contrib.contenttypes.admin import GenericTabularInline
from django.db.models.aggregates import Count  # For aggregating data (counting related objects)
from django.db.models.query import QuerySet  # For type hinting querysets
from django.utils.html import format_html, urlencode  # For creating safe HTML links and URL encoding
from django.urls import reverse
from . import models 

class InventoryFilter(admin.SimpleListFilter):
    title = 'inventory'
    parameter_name = 'inventory'

    def lookups(self, request, model_admin):
        return [
            ('<10', 'Low'),
            ('>=10', 'OK')
        ]
    
    def queryset(self, request, queryset):
        if self.value() == '<10':
            return queryset.filter(inventory__lt=10)
        if self.value() == '>=10':
            return queryset.filter(inventory__gte=10)
        return queryset
    
# ProductAdmin: Configures how Product model appears in Django admin
@admin.register(models.Product)  # decorator helps register the model with the admin site and help with sorting
class ProductAdmin(admin.ModelAdmin):
    # Define which fields to display in the admin list view
    autocomplete_fields = ['collection']  # Enable autocomplete for collection field
    prepopulated_fields = {
        'slug': ['title']
        }  # Auto-fill slug field based on title
    actions = ['clear_inventory']
    list_display = ['title', 'unit_price', 'inventory_status', 'collection_title']
    list_editable = ['unit_price']  
    list_per_page = 10
    list_filter = ['collection', 'last_update', InventoryFilter]  # Add filter sidebar for collections
    list_select_related = ['collection']  # Optimize database queries by fetching related collection data in one query
    search_fields = ['title']  # Add search box for title field

    # Custom method to display the collection title for each product
    def collection_title(self, product):
        return product.collection.title
    
    # Custom method to show inventory status with conditional logic
    @admin.display(ordering='inventory')  # @admin.display makes this field sortable by 'inventory' field
    def inventory_status(self, product):
        if product.inventory < 10:
            return 'Low'
        return 'OK'

    @admin.action(description='Clear inventory')  # Decorator to set action description in admin UI
    def clear_inventory(self, request, queryset):
        # Clear inventory for selected products
        updated_count = queryset.update(inventory=0)
        self.message_user(
            request, 
            f"Inventory cleared for {updated_count} products.",
            messages.ERROR
        )

# CollectionAdmin: Manages Collection model with product count functionality
@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'products_count']
    search_fields = ['title']

    # Custom method to display product count as a clickable link
    @admin.display(ordering='products_count')
    def products_count(self, collection):
        # Build URL to product admin page filtered by this collection
        url = (
            reverse('admin:store_product_changelist')  # Get the product admin list URL
            + '?' 
            + urlencode({'collection__id__exact': str(collection.id)})  # Add filter parameters
        )
        # Return HTML link with the count as clickable text
        return format_html("<a href='{}'>{}</a>", url, collection.products_count)

    # Override queryset to add product count annotation
    # This prevents N+1 queries by calculating counts at database level
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(  
            products_count=Count('product')  # Count related products for each collection
        ) 

# CustomerAdmin: Manages Customer model with order count functionality
@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'membership', 'orders_count']
    list_editable = ['membership']
    list_per_page = 10
    ordering = ['first_name', 'last_name']
    search_fields =['first_name__istartswith', 'last_name__istartswith']

    # Custom method to display order count as a clickable link
    # @admin.display makes this field sortable by the annotated 'orders_count'
    @admin.display(ordering='orders_count')
    def orders_count(self, customer):
        # Build URL to order admin page filtered by this customer
        url = (
            reverse('admin:store_order_changelist')  # Get the order admin list URL
            + '?'
            + urlencode({'customer__id__exact': str(customer.id)})  # Add filter parameters
        )
        # Return HTML link with the count as clickable text
        return format_html("<a href='{}'>{}</a>", url, customer.orders_count)

    # Override queryset to add order count annotation
    # This prevents N+1 queries by calculating counts at database level
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            orders_count=Count('order')  # Count related orders for each customer
        )
    
class OrderItemInline(admin.TabularInline):
    autocomplete_fields = ['product']
    model = models.OrderItem
    extra = 0
    min_num = 1
    max_num = 10
   

# OrderAdmin: Basic configuration for Order model admin interface
@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    # Display key order information in list view
    list_display = ['id', 'placed_at','customer', 'payment_status']
    inlines = [OrderItemInline]
    autocomplete_fields = ['customer']  # Enable autocomplete for customer field