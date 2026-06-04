import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import base64
import json

# --- CONFIGURAÇÃO DE ACESSO SEGURA VIA BASE64 ---
scopes = ['https://www.googleapis.com/auth/calendar']

try:
    # Lendo o texto codificado em Base64 dos Secrets do Streamlit
    encoded_json = st.secrets["gcp_service_account"]["ambiente_chave"]
    
    # Decodificando de volta para o formato JSON original do Google
    decoded_json = base64.b64decode(encoded_json).decode("utf-8")
    info_dict = json.loads(decoded_json)
    
    # Conectando à API do Google Calendar
    credentials = service_account.Credentials.from_service_account_info(info_dict, scopes=scopes)
    service = build('calendar', 'v3', credentials=credentials)
except Exception as e:
    st.error(f"Erro na conexão com o Google: {e}")
    st.info("Certifique-se de que colou o código Base64 corretamente nos Secrets do Streamlit.")
    st.stop()

# ID da agenda (Usa-se 'primary' para a agenda principal do e-mail compartilhado)
AGENDA_ID = 'primary' 

# --- INTERFACE DO UTILIZADOR (STREAMLIT) ---
st.set_page_config(page_title="Agenda Massoterapia", page_icon="💆‍♀️")

st.title("💆‍♀️ Sistema de Agendamento de Massoterapia")
st.write("Preencha os dados abaixo para reservar o seu horário de atendimento.")

nome = st.text_input("Nome da Cliente")
data = st.date_input("Escolha a Data")
hora = st.time_input("Escolha o Horário")
telefone = st.text_input("WhatsApp da Cliente (ex: 51999999999)")

if st.button("Confirmar Agendamento"):
    if nome and telefone:
        # Calcular início e fim do atendimento (considerando 1 hora de duração)
        # Configurado para o fuso horário de Brasília/Porto Alegre (-03:00)
        start_dt = datetime.combine(data, hora)
        end_dt = start_dt + timedelta(hours=1)
        
        start_time = start_dt.isoformat() + "-03:00"
        end_time = end_dt.isoformat() + "-03:00"
        
        # --- BLOCO DE VALIDAÇÃO DE CONFLITOS (OVERBOOKING) ---
        try:
            events_result = service.events().list(
                calendarId=AGENDA_ID,
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True
            ).execute()
            
            eventos_existentes = events_result.get('items', [])
            
            # Se encontrar algum evento neste horário, bloqueia o agendamento
            if eventos_existentes:
                st.error("⚠️ Ops! Este horário não está disponível. Já existe um compromisso marcado. Por favor, escolha outro horário.")
            else:
                # Criar a estrutura do evento para o Google Calendar
                event = {
                    'summary': f'Massagem: {nome}',
                    'description': f
