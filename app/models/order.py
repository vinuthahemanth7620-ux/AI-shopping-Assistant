import enum
from datetime import datetime
from app import db


class OrderStatus(str, enum.Enum):
    """Enumeration for Order Statuses."""
    PENDING = 'Pending'
    PROCESSING = 'Processing'
    SHIPPED = 'Shipped'
    DELIVERED = 'Delivered'
    CANCELLED = 'Cancelled'


class Order(db.Model):
    """
    Order Model representing placed user purchases.
    Table: orders
    """
    __tablename__ = 'orders'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Unique Order Number
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # Foreign Key -> User (Indexed)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Order Financial Metrics
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)

    # Status Control
    status = db.Column(
        db.Enum(OrderStatus, name='order_statuses'),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True
    )

    # Shipping Information
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    payment_method = db.Column(db.String(50), default='Cash on Delivery', nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    @property
    def total_amount_formatted(self):
        """Get formatted string representation of total order amount in INR."""
        amt = float(self.total_amount or 0.0)
        return f"₹{amt:,.2f}"

    def to_dict(self):
        """Convert model instance into dictionary format for API serialization."""
        status_str = self.status.value if hasattr(self.status, 'value') else str(self.status)
        return {
            'id': self.id,
            'order_number': self.order_number,
            'user_id': self.user_id,
            'total_amount': float(self.total_amount),
            'total_amount_formatted': self.total_amount_formatted,
            'status': status_str,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'shipping_address': self.shipping_address,
            'city': self.city,
            'postal_code': self.postal_code,
            'payment_method': self.payment_method,
            'items_count': len(self.items),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Order {self.order_number} User={self.user_id}>'


class OrderItem(db.Model):
    """
    OrderItem Model representing individual line items in a placed order.
    Table: order_items
    """
    __tablename__ = 'order_items'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    order_id = db.Column(
        db.Integer,
        db.ForeignKey('orders.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    # Line Item Details
    product_name = db.Column(db.String(255), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    @property
    def subtotal(self):
        """Calculate line item subtotal (quantity * unit_price)."""
        return self.quantity * float(self.unit_price or 0.0)

    @property
    def subtotal_formatted(self):
        """Get formatted subtotal in INR."""
        return f"₹{self.subtotal:,.2f}"

    def to_dict(self):
        """Convert model instance into dictionary format for API serialization."""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'unit_price': float(self.unit_price),
            'quantity': self.quantity,
            'subtotal': self.subtotal,
            'subtotal_formatted': self.subtotal_formatted
        }

    def __repr__(self):
        return f'<OrderItem Order={self.order_id} Product={self.product_name}>'
