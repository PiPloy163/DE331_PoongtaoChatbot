import json
import re
import boto3
import time
import http.client
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from boto3.dynamodb.conditions import Key, Attr

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = "linePoongtao"
table = dynamodb.Table(table_name)

# Set timezone for Thailand (UTC+7)
thailand_tz = timezone(timedelta(hours=7))

def lambda_handler(event, context):
    try:
        # Log incoming event
        print("Event Received:", json.dumps(event, indent=2))
        
        body = json.loads(event["body"])
        reply_token = body["events"][0]["replyToken"]
        user_message = body["events"][0]["message"]["text"]
        user_id = body["events"][0]["source"]["userId"]
        
        # Process user message
        response_message = process_message(user_message, user_id)
        
        # Prepare reply data
        post_data = json.dumps({
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "text",
                    "text": response_message
                }
            ]
        })
        
        print("Post Data Prepared:", post_data)
        
        # Send reply to LINE
        make_request(post_data)
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Processed successfully"})
        }
    
    except Exception as e:
        log_error("Unexpected error in lambda_handler", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal server error"})
        }

def process_message(message, user_id):
    """Process user message to identify income/expense and save to DynamoDB."""
    try:
        # Match patterns for income/expense with new structure
        income_pattern = re.match(r"ได้รับเงินจาก\s*(.+)\s+(\d+(\.\d{1,2})?)", message)
        expense_pattern = re.match(r"จ่ายค่า\s*(.+)\s+(\d+(\.\d{1,2})?)", message)
        summary_pattern = re.match(r"สรุป", message)  # Detect "สรุป" keyword
        
        if income_pattern:
            note = income_pattern.group(1)  # Extract note
            amount = Decimal(income_pattern.group(2)).quantize(Decimal('0.01'))  # Extract amount
            save_to_dynamodb(user_id, "income", amount, note)
            return f"บันทึก รายรับ {amount} บาท จาก: {note} เรียบร้อยแล้ว!"
        
        elif expense_pattern:
            note = expense_pattern.group(1)  # Extract note
            amount = Decimal(expense_pattern.group(2)).quantize(Decimal('0.01'))  # Extract amount
            save_to_dynamodb(user_id, "expense", amount, note)
            return f"บันทึก รายจ่าย {amount} บาท ให้กับ: {note} เรียบร้อยแล้ว!"
        
        elif summary_pattern:
            # Get summary for the user
            summary = get_summary_from_dynamodb(user_id)
            return summary
        
        else:
            return "กรุณาพิมพ์ตามรูปแบบ เช่น 'ได้รับเงินจาก<แฟนจ๋า> <3000>' หรือ 'จ่ายค่า<ข้าวเช้า> <70.75>' หรือ 'สรุป' เพื่อดูสรุปรายรับรายจ่าย"
    
    except Exception as e:
        log_error("Error in process_message", e)
        return "เกิดข้อผิดพลาดในการประมวลผลข้อความ"

def save_to_dynamodb(user_id, record_type, amount, note):
    """Save income/expense record to DynamoDB, including user_id and date."""
    try:
        # Generate transaction_id based on user_id and timestamp
        transaction_id = f"{record_type}-{user_id}-{int(time.time())}"
        
        # Get current date and time for record in Thailand timezone
        thailand_time = datetime.now(thailand_tz)
        current_date = thailand_time.strftime("%Y-%m-%d")
        current_time = thailand_time.strftime("%H:%M")  # Current time in HH:MM format
        
        # Save the data to DynamoDB
        response = table.put_item(
            Item={
                "user_id": user_id,
                "transaction_id": transaction_id,
                "type": record_type,
                "amount": str(amount),  # Store amount as string to preserve decimal precision
                "note": note,
                "timestamp": int(time.time()),
                "date": current_date,  # Store the date in YYYY-MM-DD format
                "time": current_time  # Store the time in HH:MM format
            }
        )
        
        # Log success or failure of DynamoDB operation
        if response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
            print(f"Data successfully saved to DynamoDB: {record_type} - {amount} บาท for user {user_id}")
        else:
            print(f"Failed to save data to DynamoDB: {record_type} - {amount} บาท for user {user_id}")
    
    except Exception as e:
        log_error("Error in save_to_dynamodb", e)

def get_summary_from_dynamodb(user_id):
    """Retrieve and summarize income/expense data from DynamoDB for a specific user."""
    try:
        # Get today's date for filtering
        today_date = datetime.now(thailand_tz)
        day = today_date.strftime("%d")  # Day as a number
        month = today_date.strftime("%B")  # Month as a name
        year = today_date.strftime("%Y")  # Year

        # Convert month to Thai language
        thai_months = {
            "January": "มกราคม", "February": "กุมภาพันธ์", "March": "มีนาคม",
            "April": "เมษายน", "May": "พฤษภาคม", "June": "มิถุนายน",
            "July": "กรกฎาคม", "August": "สิงหาคม", "September": "กันยายน",
            "October": "ตุลาคม", "November": "พฤศจิกายน", "December": "ธันวาคม"
        }
        month_in_thai = thai_months.get(month, month)  # Convert to Thai month name

        # Query the DynamoDB table for records by user_id and today's date
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id),
            FilterExpression=Attr('date').eq(today_date.strftime("%Y-%m-%d"))
        )
        
        income_total_today = Decimal(0)
        expense_total_today = Decimal(0)
        
        # Sum up the amounts for income and expenses
        for item in response.get('Items', []):
            if item['type'] == 'income':
                income_total_today += Decimal(item['amount'])
            elif item['type'] == 'expense':
                expense_total_today += Decimal(item['amount'])
        
        # Calculate today's net balance
        net_balance_today = income_total_today - expense_total_today
        
        
        # Calculate the final balance (yesterday's balance + today's income - today's expenses)
        final_balance = income_total_today - expense_total_today
        
        # Format the response message with the totals
        summary_message = (
            f"สรุปรายการของคุณในวันที่ {day} {month_in_thai} {year}\n"
            f"รายรับวันนี้: {income_total_today} บาท\n"
            f"รายจ่ายวันนี้: {expense_total_today} บาท\n"
            f"เงินคงเหลือปัจจุบัน: {final_balance} บาท"
        )
        
        return summary_message
    
    except Exception as e:
        log_error("Error in get_summary_from_dynamodb", e)
        return "ไม่สามารถดึงข้อมูลสรุปได้"

def make_request(post_data):
    """Make request to the LINE API."""
    try:
        conn = http.client.HTTPSConnection("api.line.me")
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer <Channel access token>'
            #Replace the Channel Access Token provided in the Messaging API section of LINE Developers
        }
        conn.request("POST", "/v2/bot/message/reply", post_data, headers)
        response = conn.getresponse()
        print("LINE response status:", response.status)
        print("LINE response reason:", response.reason)
        conn.close()
    except Exception as e:
        log_error("Error in make_request", e)

def log_error(message, error):
    """Log error messages."""
    print(f"ERROR: {message} - {str(error)}")
