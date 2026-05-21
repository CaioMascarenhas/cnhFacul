# API CNH com Gemini

API Flask simples para estudar CNH com suporte a exercicios e chat em portuges.

## Requisitos
- Python 3.11+
- Variavel de ambiente `GEMINI_API_KEY` definida no arquivo `.env`

## Instalar
```bash
pip install -r requirements.txt
```

## Executar
```bash
python app.py
```

Depois abra no navegador:
```text
http://127.0.0.1:5000
```

Essa pagina tem botoes para testar `POST /exercicios` e `POST /chat` direto no navegador.

## Endpoints

### `POST /exercicios`
Gera exercicios de CNH com limite maximo de 10.

Exemplo de corpo:
```json
{
  "quantidade": 5
}
```

Resposta esperada:
```json
{
  "exercicios": [
    {
      "numero": 1,
      "pergunta": "...",
      "alternativas": ["A", "B", "C", "D"],
      "resposta_correta": "A",
      "explicacao": "..."
    }
  ]
}
```

### `POST /chat`
Conversa com o tutor de CNH.

Exemplo de corpo:
```json
{
  "mensagem": "Me explica sinalizacao de pare",
  "historico": [
    {"role": "user", "content": "Estou estudando para a prova teorica"},
    {"role": "model", "content": "Posso te ajudar com isso."}
  ]
}
```

Resposta esperada:
```json
{
  "resposta": "..."
}
```
