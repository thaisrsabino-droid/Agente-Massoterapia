import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta, time
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

# IMPORTANTE: Lembre-se de substituir o 'primary' pelo e-mail da sua irmã se ainda não mudou
AGENDA_ID = 'primary' 

# --- INTERFACE DO USUÁRIO (STREAMLIT) ---
st.set_page_config(page_title="Agenda Massoterapia", page_icon="💆‍♀️")

st.title("💆‍♀️ Sistema de Agendamento de Massoterapia")
st.write("Preencha os dados abaixo para reservar o seu horário.")

nome = st.text_input("Nome da Cliente")

# Calendário no formato brasileiro
data = st.date_input("Escolha a Data", format="DD/MM/YYYY")

# --- LISTA DE HORÁRIOS PERMITIDOS (INTERVALOS DE 1 HORA) ---
horarios_disponiveis = [
    "08:00", "09:00", "10:00", "11:00", "12:00", 
    "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"
]
hora_selecionada = st.selectbox("Escolha o Horário", horarios_disponiveis)

telefone = st.text_input("WhatsApp da Cliente com DDD (ex: 51999999999)")

if st.button("Confirmar Agendamento"):
    dia_semana = data.weekday()
    
    if not nome or not telefone:
        st.error("Por favor, preencha todos os campos antes de confirmar.")
    # ALTERAÇÃO AQUI: Se for maior que 4, significa que é Sábado (5) ou Domingo (6)
    elif dia_semana > 4:
        st.error("⚠️ Ops! Nossos atendimentos ocorrem exclusivamente de segunda a sexta-feira. Por favor, escolha um dia útil.")
    else:
        # Converte a string selecionada em um objeto de hora
        hora_objeto = datetime.strptime(hora_selecionada, "%H:%M").time()
        
        # Limpa o número de telefone
        telefone_limpo = "".join(filter(str.isdigit, telefone))
        
        # Garante o prefixo do país para o WhatsApp
        if not telefone_limpo.startswith("55"):
            telefone_wa = "55" + telefone_limpo
        else:
            telefone_wa = telefone_limpo

        # Configura o início e fim do evento (Duração de 1 hora)
        start_dt = datetime.combine(data, hora_objeto)
        end_dt = start_dt + timedelta(hours=1)
        
        start_time = start_dt.isoformat() + "-03:00"
        end_time = end_dt.isoformat() + "-03:00"
        
        try:
            # --- VALIDAÇÃO DE CONFLITOS ---
            events_result = service.events().list(
                calendarId=AGENDA_ID,
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True
            ).execute()
            
            eventos_existentes = events_result.get('items', [])
            
            if eventos_existentes:
                st.error(f"⚠️ Ops! O horário das {hora_selecionada} já está ocupado neste dia. Por favor, escolha outro horário.")
            else:
                # Criando o evento no Google Calendar
                event = {
                    'summary': f'Massagem: {nome}',
                    'description': f'WhatsApp: {telefone_limpo}\nAgendado automaticamente pelo site.',
                    'start': {'dateTime': start_time, 'timeZone': 'America/Sao_Paulo'},
                    'end': {'dateTime': end_time, 'timeZone': 'America/Sao_Paulo'}
                }
                
                service.events().insert(calendarId=AGENDA_ID, body=event).execute()
                st.success("🎉 Horário reservado com sucesso no Google Agenda!")
                
                # Gerador do link do WhatsApp
                data_formatada = data.strftime('%d/%m/%Y')
                msg = f"Olá {nome}, o seu horário de massoterapia está confirmado para o dia {data_formatada} às {hora_selecionada}!"
                
                link = f"https://wa.me/{telefone_wa}?text={msg.replace(' ', '%20')}"
                
                st.markdown("---")
                st.markdown(f"### [📲 Clique aqui para enviar a confirmação no WhatsApp da Cliente]({link})")
        
        except Exception as e:
            st.error(f"Ocorreu um erro ao acessar o Google Agenda: {e}")
