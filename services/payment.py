import requests
import base64
import secrets
import time
from datetime import datetime
from config import Config

class PaymentService:
    def __init__(self):
        self.server_key = Config.MIDTRANS_SERVER_KEY
        self.client_key = Config.MIDTRANS_CLIENT_KEY
        self.snap_url = Config.MIDTRANS_SNAP_URL
        self.status_url = Config.MIDTRANS_STATUS_URL
    
    def create_payment(self, cart, customer_data, base_url):
        """Create Midtrans payment transaction"""
        try:
            print(f"Creating payment with cart: {cart}")
            print(f"Customer data: {customer_data}")
            
            # Validate cart is not empty
            if not cart or len(cart) == 0:
                return {'success': False, 'error': 'Cart is empty'}
            
            # Calculate total and ensure it's valid
            total = 0
            for item in cart:
                if 'total' not in item or not isinstance(item['total'], (int, int)):
                    print(f"Invalid item total: {item}")
                    return {'success': False, 'error': f'Invalid item total for {item.get("name", "unknown item")}'}
                total += int(item['total'])
            
            if total <= 0:
                return {'success': False, 'error': 'Cart total must be greater than 0'}
            
            # Convert to integer (Midtrans requirement)
            total_int = int(round(total))
            print(f"Calculated total: {total} -> {total_int}")
            
            # Generate unique order ID
            order_id = f"ORDER-{int(time.time())}-{secrets.token_hex(4)}"
            
            # Prepare item details with strict validation
            item_details = []
            for i, item in enumerate(cart):
                try:
                    # Validate required fields
                    if 'id' not in item or 'name' not in item or 'price' not in item or 'quantity' not in item:
                        print(f"Missing required fields in item {i}: {item}")
                        return {'success': False, 'error': f'Invalid item data: missing required fields'}
                    
                    item_price = int(item['price'])
                    item_quantity = int(item['quantity'])
                    
                    if item_price <= 0 or item_quantity <= 0:
                        return {'success': False, 'error': f'Invalid price or quantity for {item["name"]}'}
                    
                    item_detail = {
                        "id": str(item['id'])[:50],  # Ensure string and limit length
                        "price": int(round(item_price)),  # Ensure integer
                        "quantity": item_quantity,  # Ensure integer
                        "name": str(item['name'])[:50]  # Limit name length and ensure string
                    }
                    item_details.append(item_detail)
                    print(f"Added item detail: {item_detail}")
                    
                except (ValueError, KeyError) as e:
                    print(f"Error processing item {i}: {e}")
                    return {'success': False, 'error': f'Invalid item data: {str(e)}'}
            
            # Validate customer data
            if not customer_data.get('name', '').strip():
                return {'success': False, 'error': 'Customer name is required'}
            if not customer_data.get('phone', '').strip():
                return {'success': False, 'error': 'Customer phone is required'}
            
            customer_name = str(customer_data.get('name', 'Customer')).strip()[:50]
            customer_email = str(customer_data.get('email', 'customer@example.com')).strip()[:50]
            customer_phone = str(customer_data.get('phone', '08123456789')).strip()
            
            # Ensure phone number format (Indonesian format)
            customer_phone = ''.join(filter(str.isdigit, customer_phone))  # Remove non-digits
            if not customer_phone:
                return {'success': False, 'error': 'Invalid phone number format'}
            if not customer_phone.startswith('0'):
                customer_phone = '0' + customer_phone
            
            # Validate email format (basic)
            if '@' not in customer_email:
                customer_email = 'customer@example.com'
            
            payment_payload = {
                "transaction_details": {
                    "order_id": order_id,
                    "gross_amount": total_int
                },
                "customer_details": {
                    "first_name": customer_name,
                    "email": customer_email,
                    "phone": customer_phone
                },
                "item_details": item_details,
                "callbacks": {
                    "finish": f"{base_url}/order-success/{order_id}"
                }
            }
            
            # Debug: Print payload
            print(f"Final Midtrans Payload: {payment_payload}")
            print(f"Total items: {len(item_details)}")
            print(f"Gross amount: {total_int}")
            
            # Validate payload before sending
            if total_int <= 0:
                return {'success': False, 'error': 'Invalid total amount'}
            if not item_details:
                return {'success': False, 'error': 'No items in cart'}
            
            # Prepare headers
            if not self.server_key:
                return {'success': False, 'error': 'Midtrans server key not configured'}
                
            encoded_key = base64.b64encode(f"{self.server_key}:".encode()).decode()
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f'Basic {encoded_key}'
            }
            
            print(f"Making request to: {self.snap_url}")
            print(f"Headers: {headers}")
            
            # Make request to Midtrans
            response = requests.post(
                self.snap_url,
                json=payment_payload,
                headers=headers,
                timeout=30
            )
            
            # Debug: Print response details
            print(f"Midtrans Response Status: {response.status_code}")
            print(f"Midtrans Response Headers: {response.headers}")
            print(f"Midtrans Response Text: {response.text[:500]}...")  # First 500 chars
            
            if response.status_code == 201:
                try:
                    result = response.json()
                    return {
                        'success': True,
                        'snap_token': result['token'],
                        'order_id': order_id
                    }
                except ValueError as json_error:
                    print(f"JSON Parse Error: {json_error}")
                    return {
                        'success': False,
                        'error': f'Invalid JSON response from payment service: {response.text[:200]}'
                    }
            else:
                # Try to parse error response
                try:
                    error_data = response.json()
                    error_message = error_data.get('error_messages', [response.text])
                    if isinstance(error_message, list):
                        error_message = ', '.join(error_message)
                except:
                    error_message = response.text
                
                return {
                    'success': False,
                    'error': f'Payment creation failed (HTTP {response.status_code}): {error_message}'
                }
        
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Payment service timeout - please try again'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Cannot connect to payment service - check internet connection'}
        except Exception as e:
            print(f"Payment creation exception: {str(e)}")
            return {'success': False, 'error': f'Payment creation error: {str(e)}'}
    
    def verify_payment_status(self, order_id):
        """Verify payment status with Midtrans API"""
        try:
            encoded_key = base64.b64encode(f"{self.server_key}:".encode()).decode()
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Basic {encoded_key}'
            }
            
            response = requests.get(
                f'{self.status_url}/{order_id}/status',
                headers=headers,
                timeout=10
            )
            
            print(f"Payment verification response: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    transaction_status = result.get('transaction_status')
                    return transaction_status in ['settlement', 'capture', 'pending']
                except ValueError:
                    print(f"Payment verification JSON parse error: {response.text}")
                    return False
            
            return False
        
        except Exception as e:
            print(f"Payment verification error: {str(e)}")
            return False