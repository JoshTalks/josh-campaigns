# 🧪 Template Testing & Preview Guide

## 🎯 **Where to Test Templates**

### **1. Template Management Page** (`/outreach/manage-templates/`)
- **Create new templates** with variable placeholders
- **Test any existing template** with the 🧪 "Test Template" button
- **Preview templates** with the 👁️ "Preview" button

### **2. Template Detail Page** (`/outreach/template-detail/<id>/`)
- **Edit existing templates** and test them immediately
- **Use the 🧪 "Test Template" button** to test your changes

### **3. Campaign Creation Page** (`/outreach/create-campaign/`)
- **Select templates** and see real-time previews
- **Test variable replacement** with custom values
- **Multiple preview tabs**: HTML, Text, and MSG91 previews

## 🔧 **How to Use Template Variables**

### **Variable Syntax**
Use double curly braces for placeholders:
```
Hello {{name}},

Your verification code is: {{otp}}

Please visit: {{login_url}}

Best regards,
{{company_name}} Team
```

### **Common Variables**
- `{{name}}` - Customer full name
- `{{email}}` - Customer email address
- `{{phone}}` - Customer phone number
- `{{company}}` - Company name
- `{{otp}}` - One-time password
- `{{verification_code}}` - Verification code
- `{{reset_link}}` - Password reset link
- `{{login_url}}` - Login page URL
- `{{website_url}}` - Website URL
- `{{support_email}}` - Support email
- `{{address}}` - Customer address
- `{{job_link}}` - Job profile link

## 🧪 **Testing Templates Step by Step**

### **Step 1: Create/Edit Template**
1. Go to `/outreach/manage-templates/`
2. Fill in template details (name, channel, subject, content)
3. Use variables like `{{name}}`, `{{email}}`, etc.

### **Step 2: Test Template**
1. Click the 🧪 **"Test Template"** button
2. A modal will open showing:
   - Template details
   - Variable input fields with sample values
   - Preview tabs (Original vs. Preview)

### **Step 3: Customize Variables**
1. **Edit the sample values** in the input fields
2. Click **"Preview with Custom Values"**
3. See your template with **real values** instead of placeholders

### **Step 4: Review Preview**
- **Original Tab**: Shows template with highlighted variables
- **Preview Tab**: Shows template with your custom values
- **Switch between tabs** to compare

## 📱 **Template Preview Features**

### **Real-time Preview**
- **Live updates** as you type in the form
- **Variable highlighting** with colored badges
- **Channel-specific fields** (subject for email, hidden for SMS/WhatsApp)

### **Multiple Preview Modes**
1. **HTML Preview**: Shows formatted HTML with variables
2. **Text Preview**: Clean text version for readability
3. **MSG91 Preview**: Visual preview from MSG91 API (if available)

### **Variable Testing**
- **Sample data** automatically populated
- **Custom values** for testing
- **Real-time replacement** in preview
- **Validation** for required fields

## 🚀 **Quick Start Examples**

### **Example 1: Welcome Email**
```
Subject: Welcome to {{company_name}}, {{name}}!

Hi {{name}},

Welcome to {{company_name}}! Your account has been created successfully.

Your login details:
- Username: {{email}}
- Login URL: {{login_url}}

If you have any questions, contact us at {{support_email}}.

Best regards,
{{company_name}} Team
```

### **Example 2: OTP Verification**
```
Subject: Your verification code: {{otp}}

Hi {{name}},

Your verification code is: {{otp}}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this message.

Best regards,
{{company_name}} Team
```

### **Example 3: Job Application**
```
Subject: Application received from {{name}}

Hi {{name}},

Thank you for your application to {{company_name}}.

We have received your application and will review it shortly.

Your application details:
- Position: {{position}}
- Applied on: {{date}}
- Profile: {{job_link}}

We'll contact you at {{email}} or {{phone}}.

Best regards,
{{company_name}} HR Team
```

## 🔍 **Troubleshooting**

### **Template Not Showing Variables**
- Check that variables use `{{variable_name}}` syntax
- Ensure no extra spaces in variable names
- Variables are case-sensitive

### **Preview Not Working**
- Make sure you have template content
- Check browser console for JavaScript errors
- Verify all required fields are filled

### **Variables Not Replacing**
- Check variable syntax matches exactly
- Ensure no typos in variable names
- Variables must be in double curly braces

## 💡 **Pro Tips**

1. **Test First**: Always test templates before using in campaigns
2. **Use Descriptive Names**: Make variable names clear and meaningful
3. **Sample Data**: Use realistic sample values for better testing
4. **Multiple Scenarios**: Test with different variable combinations
5. **Mobile Preview**: Check how templates look on mobile devices

## 🎉 **Ready to Test!**

Now you have a comprehensive template testing system! Use the 🧪 "Test Template" buttons throughout the application to:

- ✅ **Preview templates** with sample data
- ✅ **Test variable replacement** with custom values
- ✅ **See real-time updates** as you edit
- ✅ **Validate templates** before using in campaigns

Happy template testing! 🚀
