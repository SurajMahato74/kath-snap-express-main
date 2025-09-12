# Cart System Setup

## Backend Setup

1. **Run Migrations**
   ```bash
   cd backend/ezeyway
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Start Django Server**
   ```bash
   python manage.py runserver
   ```

## Frontend Setup

1. **Install Dependencies** (if not already done)
   ```bash
   cd kath-snap-express-main
   npm install
   ```

2. **Start React App**
   ```bash
   npm run dev
   ```

## Cart API Endpoints

- `GET /api/cart/` - Get user's cart
- `POST /api/cart/add/` - Add item to cart
- `PUT /api/cart/items/{item_id}/update/` - Update cart item quantity
- `DELETE /api/cart/items/{item_id}/remove/` - Remove item from cart
- `DELETE /api/cart/clear/` - Clear entire cart

## Features Added

### Backend
- **Cart Model**: Stores user cart information
- **CartItem Model**: Stores individual cart items with product and quantity
- **Cart APIs**: Complete CRUD operations for cart management
- **Cart Serializers**: Proper data serialization for API responses

### Frontend
- **Cart Service**: API communication layer
- **useCart Hook**: React hook for cart state management
- **Dynamic Cart Page**: Fully functional cart with real data
- **Loading States**: Proper loading indicators
- **Error Handling**: Toast notifications for errors

## Usage

1. **Authentication Required**: Users must be logged in to use cart features
2. **Add to Cart**: Use the cart service to add products
3. **Update Quantities**: Click +/- buttons to update item quantities
4. **Remove Items**: Click trash icon to remove items
5. **Select Items**: Use checkboxes to select items for checkout

## Database Schema

### Cart Table
- `id` (Primary Key)
- `user_id` (Foreign Key to CustomUser)
- `created_at`
- `updated_at`

### CartItem Table
- `id` (Primary Key)
- `cart_id` (Foreign Key to Cart)
- `product_id` (Foreign Key to Product)
- `quantity`
- `created_at`
- `updated_at`

## API Response Format

```json
{
  "id": 1,
  "items": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "name": "Product Name",
        "price": 100.00,
        "images": [...],
        "vendor_name": "Vendor Name"
      },
      "quantity": 2,
      "total_price": 200.00
    }
  ],
  "total_items": 2,
  "subtotal": 200.00
}
```