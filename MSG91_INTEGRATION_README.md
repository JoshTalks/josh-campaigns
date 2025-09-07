# MSG91 Email Integration for Josh Campaigns

This document explains how to set up and use MSG91 for sending email campaigns in your Josh Campaigns application.

## Overview

MSG91 is a communication platform that provides email, SMS, and WhatsApp services. This integration adds MSG91 email support to your existing campaign system, allowing you to send emails through MSG91's API alongside your existing SendGrid integration.

## Features

- ✅ Send individual emails through MSG91 API
- ✅ Send bulk emails for campaigns
- ✅ Retrieve MSG91 email templates
- ✅ Test MSG91 API connection
- ✅ Admin interface integration
- ✅ Web-based testing interface
- ✅ Fallback to SendGrid for non-MSG91 campaigns

## Setup Instructions

### 1. Environment Configuration

Add the following environment variables to your `.env` file:

```bash
# MSG91 Configuration for Email Campaigns
MSG91_AUTH_KEY=your-msg91-auth-key-here
MSG91_EMAIL_FROM=noreply@yourdomain.com
MSG91_EMAIL_FROM_NAME=Your Company Name
```

### 2. Install Dependencies

The integration requires the `requests` library. Install it using:

```bash
pip install requests
```

Or update your requirements.txt and run:

```bash
pip install -r requirements.txt
```

### 3. MSG91 Account Setup

1. **Create MSG91 Account**: Sign up at [MSG91](https://msg91.com/)
2. **Get API Key**: Navigate to your dashboard and copy your authentication key
3. **Verify Email Domain**: Add and verify your sender email domain in MSG91
4. **Enable Email Service**: Ensure email service is activated in your MSG91 account

## Usage

### Creating MSG91 Email Campaigns

1. **Navigate to Campaign Creation**: Go to "Create Campaign" in your dashboard
2. **Select Channel**: Choose "Email" as the channel
3. **Select Provider**: Choose "MSG91 Email" as the provider
4. **Configure Campaign**: Set your subject, content, and select customers
5. **Send Campaign**: The system will automatically use MSG91 API to send emails

### Testing MSG91 Integration

#### Web Interface
1. Go to `/test-msg91/` in your application
2. Click "Test MSG91 Connection" to verify API connectivity
3. View configuration details and test results

#### Admin Interface
1. Access Django admin at `/admin/`
2. Go to Campaigns section
3. Select MSG91 email campaigns
4. Use "Test MSG91 integration" action

#### Command Line
```bash
# Test connection
python manage.py test_msg91 --test-connection

# List templates
python manage.py test_msg91 --list-templates

# Send test email
python manage.py test_msg91 --test-email your@email.com
```

## API Endpoints

The integration uses the following MSG91 API endpoints:

- **Send Email**: `POST /api/v5/email/send`
- **Get Templates**: `GET /api/v5/email/templates`

## Configuration Options

### Settings in `settings.py`

```python
# MSG91 Configuration for Email Campaigns
MSG91_AUTH_KEY = os.environ.get('MSG91_AUTH_KEY', 'your-default-key')
MSG91_EMAIL_ENDPOINT = "https://control.msg91.com/api/v5/email"
MSG91_EMAIL_FROM = os.environ.get('MSG91_EMAIL_FROM', 'noreply@yourdomain.com')
MSG91_EMAIL_FROM_NAME = os.environ.get('MSG91_EMAIL_FROM_NAME', 'Your Company Name')
```

### Campaign Provider Options

When creating campaigns, you can now select:
- `msg91-email` - Use MSG91 for email sending
- `twilio-sendgrid` - Use SendGrid (existing)
- `aws-ses` - Use AWS SES (existing)

## Message Delivery Flow

1. **Campaign Creation**: User creates campaign with MSG91 email provider
2. **Message Processing**: System processes campaign and creates message records
3. **MSG91 API Call**: For each customer, system calls MSG91 API
4. **Status Update**: Message status updated based on API response
5. **Campaign Completion**: Campaign marked as completed when all messages processed

## Error Handling

The integration includes comprehensive error handling:

- **Network Errors**: Connection timeouts and network issues
- **API Errors**: MSG91 API response errors
- **Authentication Errors**: Invalid API key or permissions
- **Rate Limiting**: Automatic retry logic for failed requests

## Monitoring and Logging

All MSG91 operations are logged with:
- Success/failure status
- Error messages and details
- API response information
- Customer and campaign context

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify your MSG91 API key is correct
   - Ensure your account has email permissions
   - Check if your account is active

2. **Email Not Sent**
   - Verify sender email is verified in MSG91
   - Check MSG91 account email sending limits
   - Review API response for specific error messages

3. **Connection Timeout**
   - Check your internet connection
   - Verify firewall settings allow outbound HTTPS
   - Check MSG91 service status

### Debug Mode

Enable debug logging by setting `DEBUG=True` in your Django settings. This will provide detailed information about MSG91 API calls and responses.

## Security Considerations

- **API Key Protection**: Never commit API keys to version control
- **Environment Variables**: Use environment variables for sensitive configuration
- **HTTPS Only**: All MSG91 API calls use HTTPS
- **Input Validation**: Customer data is validated before sending

## Performance

- **Bulk Sending**: Support for sending multiple emails efficiently
- **Rate Limiting**: Built-in delays to avoid overwhelming MSG91 API
- **Async Processing**: Integration with Celery for background processing
- **Connection Pooling**: Efficient HTTP connection management

## Support

For issues with MSG91 integration:

1. Check the logs for detailed error information
2. Test connection using the provided tools
3. Verify MSG91 account configuration
4. Contact MSG91 support for API-related issues

## Future Enhancements

Planned improvements include:
- Template synchronization with MSG91
- Advanced analytics and reporting
- A/B testing capabilities
- Automated retry mechanisms
- Webhook integration for delivery status

---

For more information about MSG91, visit [https://msg91.com/](https://msg91.com/)
