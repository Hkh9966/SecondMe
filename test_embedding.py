import numpy as np
import requests
import json

group_id = "2030207429425242386"
api_key = "sk-cp-ouQZFg3bZzxdJihWc9aWYv_ZNNlwESLlRpmgwb40WEED3tXbXRZydkWWD_EUnt_OfjreM8dcwXGueBH905vYlyX8-J3EXh9oPiwx1l5MJnuR83Fc9UmDi1Y"

# 从文本中提取embedding
def get_embedding(text, emb_type):
    url = f"https://api.minimax.chat/v1/embeddings?GroupId={group_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "texts": [
            text
        ],
        "model": "embo-01",
        "type": emb_type
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    res = json.loads(response.text)['vectors'][0]
    return res

# 计算两个embedding的相似度
def embedding_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

class Memory():
    def __init__(self, emb_func=get_embedding, sim_func=embedding_similarity):
        self.data = []
        self.emb_func = emb_func
        self.sim_func = sim_func
    #将分块text以及分块text形成的向量形成一个字典做关联存放在内存中，注意：当在实际应用时，应将数据存放到向量数据库中         
    def save_memory(self, text):
        embedding = self.emb_func(text, emb_type='db')
        
        self.data.append({
            "text": text,
            "emb": embedding
        })
    #根据query找出topk的分块text出来    
    def retrive(self, query, topk=2):
        query_emb = self.emb_func(query, emb_type='query')
        memory = sorted(self.data, key=lambda x: self.sim_func(x['emb'], query_emb), reverse=True)[:topk]
        texts = [m['text'] for m in memory]
        texts = [''] + texts + ['']
        return '\n----\n'.join(texts)

#不使用embedding进行chatcompletion接口访问               
def simple_chat(query):
    url = f"https://api.minimax.chat/v1/text/chatcompletion?GroupId={group_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "abab5-chat",
        "prompt": "你是MiniMax自主研发的大型语言模型，回答问题简洁有条理。",
        "role_meta": {
            "user_name": "用户",
            "bot_name": "智能助理"
        },
        "messages": [
            {
                "sender_type": "USER",
                "text": query
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.text

#使用embedding进行chatcompletion接口访问       
def embedding_chat(query):
    # 构建向量库
    texts = [
        'Minimax的文本embedding可用于将离散的符号（例如单词、字符或词组）映射到低维向量空间中的实数向量。这些向量的空间位置被设计为与它们语义上的关联度相关，从而可以通过进行向量的计算来比较自然语言的相似度，用于衡量文本字符串的相关性（两个向量之间的距离衡量它们的相关性，小距离表示高相关性，大距离表示低相关性）。',
        
        '由于目前模型上下文长度会锁定在特定长度（当前是4096token），因此在使用全量信息进行提问的场景下，局限性会很大。而基于embedding技术，我们可以获得两段文本之间的相似度/关联性，基于此可以实现如长记忆检索、知识库检索等能力。',
        
        '接口支持基于自然语言交互生成回复的能力。接口本身为无状态接口，即单次调用时，模型所接收到的信息量仅为接口传入内容，不涉及业务逻辑，同时模型也不存储您传入的数据。如果输入内容或输出内容严重违规，接口会返回内容违规错误信息，回复内容为空。',
        
        '针对abab5，我们为您设定了默认智能助理背景，该设定已完成绝大多数生产力场景能力调试，建议无特殊使用目的的使用者直接使用该背景设定。如果您希望直接使用默认设定，请在调用接口时不传入prompt和role_meta。',
        
        '基于MiniMax端到端自研多模态大语言模型，我们为企业用户或企业开发者提供功能丰富的API，适用于大多数文本处理的场景，以自然语言交互的形式帮助企业用户或企业开发者提高文本相关的生产效率，例如不同行业的文本续写、文案生成、文本扩写、文本改写、内容摘要、代码生成、知识检索等。',
        
        '同时我们的新一代语音合成引擎是一项创新性的技术，它依托于新一代AI大模型能力，能够理解人类语言中的复杂含义，如情感，语气，甚至笑声，从而从文本中预测出情绪、语调等信息，生成接近于人类的超自然、高保真、个性化的语音。同时，依托大语言模型架构，模型能在几GB的参数中学习到数千个声音的音色特征，从而能够在不到30秒的音频中实现音色克隆，生成与提供的音频音色特征高度相似的语音。我们的语音合成引擎能够广泛应用于电子书、游戏、客服、政府等各种场景，为用户提供更加智能、高效的语音服务。',
        
        '在大语言模型中，token是指自然语言文本中的最小粒度单位，也就是一个最小的单词或符号。通常情况下，自然语言文本是由一个一个的token组成的，每个token都具备自己的词性、词义等属性。',
        
        '在训练大语言模型时，会使用一种称为“词向量”的技术，将每个token表示成一个向量形式，这个向量可以包含很多有用的语义信息，比如单词的词性、上下文等。模型通过这些向量来学习和理解自然语言文本，并能够完成各种任务。',
        
        '在大语言模型处理任务的过程中，输入的文本会被转译为token输入到模型中，而输出则是从token转译到文本。输入token与输出token的长度直接影响了大语言模型所消耗的算力，所以业界通常采用基于token数量的计费模式。',
        
        '调用频率限制指的是基于商业策略的考量，对调用的频率进行限制的策略。',
        
        '目前限制策略主要有以下维度：基于请求次数的频率限制，按照基准时间不同，分为每秒限制请求次数（RPS）、每分钟限制请求次数（RPM）基于token数的频率限制，为每分钟限制token总量（TPM）',
        
        'minimax收费模式以每1000个token（包含输入+输出）为基础计价单位，1000个token约对应750个汉字文本（包括标点），以下是不同接口和模型及其对应价格:ChatCompletion-abab5：0.015元/千token；ChatCompletion pro-abab5.5:0.015元/千token；web search：0.03元/次调用'
    ]
    mem = Memory()
    for text in texts:
        mem.save_memory(text)
        
    # 构建回复
    context = mem.retrive(query)
    prompt = f"""使用根据以下内容来回答问题。 如果你不知道答案，就说你不知道，不要试图编造答案。
{context}
"""
    
    print(prompt)
    url = f"https://api.minimax.chat/v1/text/chatcompletion?GroupId={group_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "abab5-chat",
        "prompt": prompt,
        "role_meta": {
            "user_name": "用户",
            "bot_name": "智能助理"
        },
        "messages": [
            {
                "sender_type": "USER",
                "text": query
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.text

if __name__ == '__main__':
    query = 'ChatCompletion-abab5模型怎么计费？'
    #不使用embedding进行chatcompletion接口访问并输出回复
    print("------------------simple sample-----------------------")
    res = simple_chat(query)
    print("simple_chat result:\n", res)
    
    #使用embedding进行chatcompletion接口访问并输出回复
    print("------------------embedding sample-----------------------")
    emb_res = embedding_chat(query)
    print("embedding_chat result:\n", emb_res)