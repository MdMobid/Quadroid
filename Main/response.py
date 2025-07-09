
def generate_response(prompt):
    import openai
    from .quadpath import quadpath
    filename = 'Main\quadroid.txt'
    with open(filename,'r') as file:
        data = file.read()
    mss=[{'role':'system','content':data}]
    
    mss.append(
        {"role": "user", "content": prompt},
    )
    chat = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=mss
    )
    reply = chat.choices[0].message.content
    mss.append({"role": "assistant", "content": reply})
    return reply
