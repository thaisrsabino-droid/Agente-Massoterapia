import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import base64
import json

# --- CONFIGURAÇÃO DE ACESSO SEGURA VIA BASE64 ---
scopes = ['https://www.googleapis.com/auth/calendar']

try:
    encoded_json = st.secrets["gcp_service_account"]["ambiente_chave"]
    decoded_json = base64.b64decode(encoded_json).decode("utf-8")
    info_dict = json.loads(decoded_json)
    
    credentials = service_account.Credentials.from_service_account_info(info_dict, scopes=scopes)
    service = build('calendar', 'v3', credentials=credentials)
except Exception as e:
    st.error(f"Erro na conexão com o Google: {e}")
    st.stop()

AGENDA_ID = 'primary' 

# --- INTERFACE DO USUÁRIO (STREAMLIT) ---
st.set_page_config(page_title="Agenda Massoterapia", page_icon="💆‍♀️")

st.title("💆‍♀️ Sistema de Agendamento de Massoterapia")
st.write("Preencha os dados abaixo para reservar o seu horário.")

nome = st.text_input("Nome da Cliente")
data = st.date_input("Escolha a Data")
hora = st.time_input("Escolha o Horário")
telefone = st.text_input("WhatsApp da Cliente (ex: 51999999999)")

if st.button("Confirmar Agendamento"):
    if nome and telefone:
        start_dt = datetime.combine(data, hora)
        end_dt = start_dt + timedelta(hours=1)
        
        start_time = start_dt.isoformat() + "-03:00"
        end_time = end_dt.isoformat() + "-03:00"
        
        try:
            events_result = service.events().list(
                calendarId=AGENDA_ID,
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True
            ).execute()
            
            eventos_existentes = events_result.get('items', [])
            
            if eventos_existentes:
                st.error("⚠️ Ops! Este horário não está disponível. Já existe um compromisso marcado. Por favor, escolha outro horário.")
            else:
                # Criação do evento corrigida (tudo alinhado perfeitamente)
                event = {
                    'summary': f'Massagem: {nome}',
                    'description': f'WhatsApp: {telefone}\nAgendado automaticamente.',
                    'start': {'dateTime': start_time, 'timeZone': 'America/Sao_Paulo'},
                    'end': {'dateTime': end_time, 'timeZone': 'America/Sao_Paulo'}
                }
                
                service.events().insert(calendarId=AGENDA_ID, body=event).execute()
                st.success("🎉 Horário reservado com sucesso no Google Agenda!")
                
                # Gerador do link do WhatsApp
                msg = f"Olá {nome}, o seu horário de massoterapia está confirmado para o dia {data.strftime('%d/%m/%Y')} às {hora.strftime('%H:%M')}!"
                link = f"https://wa.me/{telefone}?text={msg.replace(' ', '%20')}"
                
                st.markdown("---")
                st.markdown(f"### [📲 Clique aqui para enviar a confirmação no WhatsApp da Cliente]({link})")
        
        except Exception as e:
            st.error(f"Ocorreu um erro ao acessar o Google Agenda: {e}")
            
    else:
        st.error("Por favor, preencha todos os campos antes de confirmar.")
