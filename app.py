import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# Configuração de acesso à API
# No topo do seu app.py
scopes = ['https://www.googleapis.com/auth/calendar']
info = st.secrets["gcp_service_account"]
credentials = service_account.Credentials.from_service_account_info(info, scopes=scopes)
service = build('calendar', 'v3', credentials=credentials)

# ID da agenda (Se for a principal da conta, usa-se 'primary')
AGENDA_ID = 'primary' 

st.title("💆‍♀️ Agenda da [Nome da Irmã]")

nome = st.text_input("Nome da Cliente")
data = st.date_input("Data")
hora = st.time_input("Horário")
telefone = st.text_input("WhatsApp (ex: 51999999999)")

if st.button("Confirmar Agendamento"):
    if nome and telefone:
        # Calcular início e fim do atendimento (considerando 1 hora de duração)
        start_time = datetime.combine(data, hora).isoformat() + "-03:00"  # Horário de Brasília
        end_time = (datetime.combine(data, hora) + timedelta(hours=1)).isoformat() + "-03:00"
        
        # --- BLOCO DE VALIDAÇÃO DE CONFLITOS ---
        # O robô lista os eventos que existem nessa janela de tempo
        events_result = service.events().list(
            calendarId=AGENDA_ID,
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True
        ).execute()
        
        eventos_existentes = events_result.get('items', [])
        
        # Se a lista NÃO estiver vazia, significa que ela já tem compromisso!
        if eventos_existentes:
            st.error("⚠️ Ops! Esse horário não está disponível. Minha irmã já possui um compromisso agendado aqui. Por favor, escolha outro horário.")
        else:
            # Se estiver livre, o robô segue o plano e cria o evento
            event = {
                'summary': f'Massagem: {nome}',
                'description': f'WhatsApp: {telefone}',
                'start': {'dateTime': start_time, 'timeZone': 'America/Sao_Paulo'},
                'end': {'dateTime': end_time, 'timeZone': 'America/Sao_Paulo'},
            }
            
            service.events().insert(calendarId=AGENDA_ID, body=event).execute()
            st.success("🎉 Agendado com sucesso!")
            
            # Gerador do link do WhatsApp para aviso
            msg = f"Olá {nome}, seu horário de massoterapia está confirmado para {data} às {hora}."
            link = f"https://wa.me/{telefone}?text={msg.replace(' ', '%20')}"
            st.markdown(f"[📲 Clique aqui para avisar a cliente pelo WhatsApp]({link})")
    else:
        st.error("Por favor, preencha todos os campos antes de confirmar.")
