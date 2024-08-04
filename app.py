from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import requests
import json

import naver
import google_map


# 앱을 사용하는 전체적인 시나리오
"""
사용자: 오늘은 날이 더운데 먹을만한거 추천해봐
ai: 시원한 날씨에는 냉면이 최고죠. 그외에도 다양한 음식들을 추천 드립니다. [냉면, 아이스크림, 빙수 ...](recommend_menu)
사용자: 주변에 냉면 파는 집 알아봐   (keysord = 냉면)
ai: (구글 지도에서 냉면을 keyword로 사용하여 검색한다.)주변에 냉면파는 곳은 A, B, C, D 등이 있습니다. 
                                                        (각각의 가게 이름, 주소, 별점(구글기준), 거리) 정보를 제공한다.  
사용자: B가 맛있어 보인다. B에서 파는 메뉴 알아와바
ai: (네이버 크롤링 사용) 식당에 있는 메뉴, 가격, 이미지 제공

끝
"""
from dotenv import load_dotenv
import os
load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
MAPS_API_KEY = os.getenv('MAPS_API_KEY')


generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}

app = Flask(__name__)

genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
  system_instruction="당신은 사용자의 입력에서 중요한 키워드를 추출하고, 필요에 따라 적절한 키워드를 추천하는 모델입니다. 추출된 키워드와 추천된 키워드는 웹 크롤링 작업에 활용됩니다. 아래의 지침을 따릅니다:\n\n**지시:**\n다음과 같은 형식으로 답변을 생성하세요.\n\n* **입력:** 사용자의 질문\n* **출력:** {entity: 엔티티 ,keyword: 키워드,  answer: 답변, recommend menu : 추천 메뉴, crawling: 크롤링}\n\n**entity:** menu, review, image 중 하나를 선택하여 출력합니다. 없을 경우 none을 출력합니다.\n**keyword:**  사용자의 입력에서 음식이나 음식점 이름을 출력합니다. 지도에서 key를 검색하는 용도로 사용하기 때문에 검색할 만한 단어로 만들어야 됩니다.\n**recommend menu:**  answer에서 음식 메뉴 이름을 출력합니다. 단 추천하지 않을 경우에는 출력하지 않습니다. 없을 경우는 출력하지 않습니다.\n**crawling:** 만약 주변(거리)와 관련된 질문일 경우 google을 출력합니다. 리뷰와 메뉴에 관련된 내용은  naver을 출력합니다. 만약 크롤링이 필요하지 않는 경우에는 none을 출력합니다.\n**answer** 너의 답변을 그냥 여기에 저장하면 되는데, 만약 사용자가 어떤 정보를 요청하면 다른 곳에서 정보를 전달하기 때문에 \"잠시만 기다려 주세요 \"라고 말해.\n\n**예시:**\n\n* **입력:** 오늘 날씨도 더운데 뭐 먹을지 추천해줘\n* **출력:** {entity: none, keyword : none ,answer: \"오늘처럼 더운 날에는 시원한 냉면이나 콩국수 어떠세요? 아니면 입맛 돋우는 새콤달콤한 비빔국수도 좋겠네요!\", recommend menu: ['냉면','콩국수','비빔국수'],crawling:none}\n\n\n* **입력:** 짜장면 맛집 추천해줘\n* **출력:** {entity: none, keyword : '짜장면',answer: 짜장면 맛집은 근처에 많습니다. '쿵후반점' 등이 있습니다., crawling: google}\n\n* **입력:** 라화쿵푸에는 어떤 메뉴가 있어?\n* **출력:** {entity: menu, keyword : 라화쿵푸, answer: 라화쿵푸에는 짜장면, 마라탕, 짬봉 등이 있습니다., crawling: naver}\n\n* **입력:** 봉피양 평양냉면 어때? \n* **출력:** {entity: review, keyword : '평양냉면', answer: 봉피양 평양냉면은 깔끔하고 담백한 맛으로 유명해요. 면발이 쫄깃하고 육수가 시원해서 많은 사람들에게 사랑받는 메뉴입니다., crawling:naver}\n\n* **입력:** 파스타 만드는 법 알려줘\n* **출력:** {entity: image, keyword : '파스타', answer: 파스타 만드는 법은 유튜브에서 '쉬운 파스타 레시피'를 검색하면 다양한 레시피를 찾아보실 수 있어요. 이미지와 함께 자세한 설명이 나와 있으니 참고해 보세요., crawling:none}\n\n**추가 지시:**\n\n* **키워드 선택:** 사용자의 질문에 가장 적합한 키워드를 선택합니다.\n* **답변:** 선택된 키워드에 맞는 구체적인 답변을 제공합니다.\n* **다양성:** 다양한 표현과 어휘를 사용하여 답변의 자연스러움을 높입니다.",
)

# 모델 대화 기록
chat_session = model.start_chat(
  history=[
  ]
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_recommendation', methods=['POST'])
def get_recommendation():
    data = request.json
    latitude = data['latitude']
    longitude = data['longitude']
    user_request = data['request']

    final_answer = {}

    # Gemini API에 요청 보내기
    try:
        response = chat_session.send_message(user_request)

        # JSON 형식 추출
        model_output = json.loads(response.text)
        print("jj", model_output)
        crawling = model_output["crawling"]
        entity = model_output["entity"]
        answer = model_output["answer"]
        recommend_menu = model_output["recommend menu"]
        keyword = model_output["keyword"]

        # 모델의 output에는 항상 answer을 포함한다.------------------------------
        final_answer["answer"] = answer
        final_answer["info"] = None
        final_answer["crawling_f"] = None
        final_answer["marker"] = None

        # 추가적인 정보를 제공할 때는 info에 담아준다.

        # ex) 오늘은 날씨가 쌀쌀한데 먹을만한거 추천해봐
        if recommend_menu and not(crawling):

            # 대답이랑 추천하는 음식들 정리한 것도 보여주기  ------------이건 수정 필요 ------------------------
            final_answer["info"] = recommend_menu
            #return recommend_menu 
        
        elif crawling:
            # 구글인 경우 주변에 있는 특정 음식 점들을 찾아주는 것이다.
            # ex) 주변에 있는 짜장면 파는 곳 알려줘
            if crawling=="google":
                nearby_restaurants_array = google_map.get_nearby_restaurants(api_key=MAPS_API_KEY, keyword=keyword, latitude=latitude, longitude=longitude)
                final_answer["info"] = nearby_restaurants_array
                final_answer["crawling_f"] = "google"
                final_answer["marker"] = "yes"

                chat_session.send_message("이건 내가 가지고 있는 정보야" + str(nearby_restaurants_array))
                #return nearby_restaurants_dict
            
            # 네이버인 경우 특정 음식점에 있는 상세 정보들을 가져오는 것이다.
            # ex) A 음식점에서 파는 메뉴 알아봐바
            elif crawling=="naver":
                naver_output = naver.extract_from_map(keyword, entity)
                final_answer["info"] = naver_output
                final_answer["crawling_f"] = "naver"
                chat_session.send_message("이건 내가 가지고 있는 정보야" + str(naver_output))
                #return naver_output
        
        #elif info:
        #    pass
        
        print(final_answer)
        return jsonify(final_answer)

    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({'error': '추천을 생성하는 중 오류가 발생했습니다. 다시 시도해 주세요.'}), 500

if __name__ == '__main__':
    app.run(debug=True)