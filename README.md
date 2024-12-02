# Poongtao Chatbot 
Chatbot for recording daily income and expenses
## LINE Official Account and stores data within AWS Cloud (DynamoDB).

### Follow the Instructions
#### Set up LINE Official Account
1. Go to LINE Developers.
2. Login with your LINE account.
3. Start the console.
4. Create a provider.
5. Create a channel by selecting "Create a Messaging API Channel".
6. Create a LINE Official Account.
7. Go to LINE Business → Create a LINE Official Account.
8. Navigate to your LINE Official Account.
9. onfigure Response Settings: Enable Chat.
10. Select Messaging API → Use the Messaging API.
11. Select the provider you created.

### Now, we can create a LINE Official Account and using the Messaging API.

#### Next Step: Go to AWS Cloud Service

1. Create a Lambda function with:
* Runtime: Python 3.8
* Architecture: arm64
2. Click Create function → Function Overview.
3. Click Add trigger.
4. Select API Gateway.
5. Create a new API with the type HTTP API.
6. Go to the API Gateway Console.
7. Create a stage and deploy the API.
8. Navigate to DynamoDB.
9. reate a table:
* Partition key: user_id (type: String)
* Sort key: transaction_id (type: String)
10. Click Create table.
11. Go back to the Lambda function.
12. Click API Gateway → Configuration.
13. Copy the API endpoint link.
14. Go back to LINE Developers → Messaging API section.
15. Under Webhook Settings, click Edit and paste the API endpoint link.
16. Click Update and Verify.
17. Scroll down to find the Channel Access Token click issue.
18. Go back to the Lambda function.
19. Paste your code into function.py under Code source.
20. Replace table_name in line 12 with your created table name.
21. Replace Channel_access_token in line 186 with the Channel Access Token from step 17.
22. Deploy the code.

### Successfully Built a LINE Chatbot!

#### Next Step: Test the Functionality

#### Go to your LINE Official Account room.
Test by typing:
- ได้รับเงินจาก<...> <จำนวนเงิน>  or
- จ่ายค่า<...> <จำนวนเงิน>

Expected Response:
- บันทึก (รายรับ/รายจ่าย) <จำนวนเงิน> (จาก/ให้กับ): ... เรียบร้อยแล้ว!"



#### Final Project DE331 Intro to cloud subject 3rd year 1st semester
Pornpimon.srt and Jiraphat.tkh