import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DE ACESSO À API ---
scopes = ['https://www.googleapis.com/auth/calendar']

# Pegamos os dados dos Secrets
info = st.secrets["gcp_service_account"]

# AJUSTE CRÍTICO: Transformamos em dicionário e corrigimos as quebras de linha da chave
info_dict = dict(info)
if "\\n" in info_dict["private_key"]:
    info_dict["private_key"] = info_dict["private_key"].replace("\\n", "\n")

try:
    credentials = service_account.Credentials.from_service_account_info(info_dict, scopes=scopes)
    service = build('calendar', 'v3', credentials=credentials)
except Exception as e:
    st.error(f"Erro na conexão com o Google: {e}")
    st.stop()

# ID da agenda (Se for a principal da conta, usa-se 'primary')
AGENDA_ID = 'primary' 

st.title("💆‍♀️ Agenda de Massoterapia")

nome = st.text_input("Nome da Cliente")
data = st.date_input("Data")
hora = st.time_input("Horário")
telefone = st.text_input("WhatsApp (ex: 51999999999)")

if st.button("Confirmar Agendamento"):
    if nome and telefone:
        # Calcular início e fim do atendimento (considerando 1 hora de duração)
        # Usamos o formato ISO com o fuso horário de Brasília (-03:00)
        start_dt = datetime.combine(data, hora)
        end_dt = start_dt + timedelta(hours=1)
        
        start_time = start_dt.isoformat() + "-03:00"
        end_time = end_dt.isoformat() + "-03:00"
        
        # --- BLOCO DE VALIDAÇÃO DE CONFLITOS ---
        try:
            events_result = service.events().list(
                calendarId=AGENDA_ID,
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True
            ).execute()
            
            eventos_existentes = events_result.get('items', [])
            
            if eventos_existentes:
                st.error("⚠️ Ops! Esse horário não está disponível. Já existe um compromisso agendado. Por favor, escolha outro horário.")
            else:
                # Criar o evento
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
                st.markdown(f"### [📲 Clique aqui para avisar a cliente pelo WhatsApp]({link})")
        
        except Exception as e:
            st.error(f"Ocorreu um erro ao acessar a agenda: {e}")
            
    else:
        st.error("Por favor, preencha todos os campos antes de confirmar.")
