import openai

def generate_response(prompt):

    mss=[{'role':'system','content':'you are a smart ai assistant and your name is Quadroid ,and you are created by Md Mobid, and you are to help humans day to day life'}]
    
    mss.append(
        {"role": "user", "content": prompt},
    )
    chat = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=mss
    )
    reply = chat.choices[0].message.content
    mss.append({"role": "assistant", "content": reply})
    return reply
