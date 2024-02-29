import streamlit as st
from openai import OpenAI
import io
import json
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from openai import OpenAI
import os


client = OpenAI(api_key=st.secrets["openaiKey"])

endpoint= st.secrets["msendpoint"]
key= st.secrets["mskey"]

load_dotenv()

def check_login(username,password):
    env_username=st.secrets["userName"]
    env_password=st.secrets["password"]
    if username==env_username and password==env_password:
        return True
    else:
        return False
    

def extract_poLine_items(uploaded_file):
    document_analysis_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    poller= document_analysis_client.begin_analyze_document("prebuilt-invoice", uploaded_file)
    invoices = poller.result()
    # st.write(invoices.content)
    poNo=None
    list=[]
    for idx, invoice in enumerate(invoices.documents):
        
        purchase_order = invoice.fields.get("PurchaseOrder")
        if purchase_order:
            poNo=purchase_order.value
        st.write("Purchase Order Number Identified: ", poNo)
        
        if not poNo or not os.path.exists("PO-JSON/"+poNo+".json"):       
            try:
                completion = client.chat.completions.create(
                            model="gpt-3.5-turbo-1106",
                            messages=[
                                {"role":"system","content":"Given to you is data of an invoice. Please extract the purchase order number from the invoice."},
                                {"role":"user","content":invoices.content},
                                {"role":"system","content":"respond in json format of key value pairs. where key will be PO {'PO':1234} , strictly follow this rule that key will be PO only"},
                                {"role":"user","content":"if you cant figure out what PO no. is make the value as None"}
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.1
                        )
                st.write(completion.choices[0].message.content)
                data = json.loads(completion.choices[0].message.content)
                poNo=data['PO']
                if poNo and os.path.exists("PO-JSON/"+poNo+".json"):
                    st.write("Purchase Order Number Identified: ", poNo)
                else:
                    st.write("Error in identifying Purchase Order Number: ", e)
                    return
            except Exception as e:
                    st.write("Error in identifying Purchase Order Number: ", e)
                    return    
            



        
        
        st.write("checking now for line items - fetching database")


        for idx, item in enumerate(invoice.fields.get("Items").value):
            tempdict={}
            
            item_description = item.value.get("Description")
            if item_description:
                
                tempdict["Description"]=item_description.value
            item_quantity = item.value.get("Quantity")
            if item_quantity:
                
                tempdict["Quantity"]=item_quantity.value
            unit = item.value.get("Unit")
            if unit:
                
                tempdict["Unit"]=unit.value
            unit_price = item.value.get("UnitPrice")
            if unit_price:
                
                tempdict["UnitPrice"]=unit_price.value
            product_code = item.value.get("ProductCode")
            if product_code:
                
                tempdict["ProductCode"]=product_code.value
            item_date = item.value.get("Date")
            if item_date:
                
                tempdict["Date"]=item_date.value
            tax = item.value.get("Tax")
            if tax:
                
                tempdict["Tax"]=tax.value
            amount = item.value.get("Amount")
            if amount:
                
                tempdict["Amount"]=amount.value
            list.append(tempdict)
        subtotal = invoice.fields.get("SubTotal")
        if subtotal:
            
            list.append({"Subtotal":subtotal.value})
        total_tax = invoice.fields.get("TotalTax")
        if total_tax:
            
            list.append({"TotalTax":total_tax.value})
        previous_unpaid_balance = invoice.fields.get("PreviousUnpaidBalance")
        if previous_unpaid_balance:
            
            list.append({"PreviousUnpaidBalance":previous_unpaid_balance.value})
        amount_due = invoice.fields.get("AmountDue")
        if amount_due:
            
            list.append({"AmountDue":amount_due.value})
        service_start_date = invoice.fields.get("ServiceStartDate")
        if service_start_date:
            
            list.append({"ServiceStartDate":service_start_date.value})

        service_end_date = invoice.fields.get("ServiceEndDate")
        if service_end_date:
            
            list.append({"ServiceEndDate":service_end_date.value})
        service_address = invoice.fields.get("ServiceAddress")
        if service_address:
            
            list.append({"ServiceAddress":service_address.value})
        service_address_recipient = invoice.fields.get("ServiceAddressRecipient")
        if service_address_recipient:
            
            list.append({"ServiceAddressRecipient":service_address_recipient.value})
        remittance_address = invoice.fields.get("RemittanceAddress")
        if remittance_address:
            
            list.append({"RemittanceAddress":remittance_address.value})
        remittance_address_recipient = invoice.fields.get("RemittanceAddressRecipient")
        if remittance_address_recipient:
            
            list.append({"RemittanceAddressRecipient":remittance_address_recipient.value})
        st.write("----------------------------------------")
    f= open("PO-JSON/"+poNo+".json",)
    data = json.load(f)
    # st.write(data['items'])
    completion = client.chat.completions.create(
                            model="gpt-3.5-turbo-1106",
                            messages=[
                                {"role":"system","content":"First provide me with line Items of the purchase order"},
                                {"role":"system","content":"below are the line items of original purchase order"+str(data['items'])},
                                {"role":"system","content":"now provide me with items present in the invoice."},
                                {"role":"system","content":"below are the line items of invoice"+str(list)},
                                {"role":"system","content":"respond in json format only, your task is to list all the items of invoice and match those with the line items of original purchase order by mentioning SL no of purchase order to track, match them using there description and name"},
                                {"role":"system","content":"Remember each item in invoice should have a corresponding item in purchase order, if not then make the value as None or show the most similar item from purchase order."}


                            ],
                            response_format={"type": "json_object"},
                            temperature=0.1
                        )
    st.write(json.loads(completion.choices[0].message.content))



def main():
    # Session state
    if 'login_status' not in st.session_state:
        st.session_state['login_status'] = False

    if st.session_state['login_status']:
        st.title("AI smartBot for Invoice Processing")

        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        if uploaded_file is not None:
            text = extract_poLine_items(uploaded_file)
            st.write("Below are the details extracted from the PDF")
            

            
                

    else:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if check_login(username, password):
                st.session_state['login_status'] = True
                st.rerun()
            else:
                st.error("Incorrect username or password")
            


if __name__ == "__main__":
    main()