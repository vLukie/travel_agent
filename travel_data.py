"""
旅行数据模块 —— 城市信息、景点、预算参考
可作为 Agent 的知识来源，也可被工具函数直接查询
"""

# 城市旅行数据库
CITIES = {
    "北京": {
        "name_en": "Beijing",
        "region": "华北",
        "best_season": "3-5月, 9-11月",
        "features": ["历史文化", "故宫", "长城", "胡同", "烤鸭"],
        "avg_cost_per_day": {
            "经济": 300,
            "舒适": 600,
            "豪华": 1200,
        },
        "attractions": [
            {"name": "故宫", "time": "半天", "ticket": 60, "type": "历史"},
            {"name": "长城(八达岭)", "time": "一天", "ticket": 40, "type": "历史"},
            {"name": "天坛", "time": "2-3小时", "ticket": 15, "type": "历史"},
            {"name": "颐和园", "time": "半天", "ticket": 30, "type": "园林"},
            {"name": "天安门广场", "time": "1小时", "ticket": 0, "type": "地标"},
            {"name": "南锣鼓巷", "time": "2小时", "ticket": 0, "type": "逛街"},
            {"name": "798艺术区", "time": "半天", "ticket": 0, "type": "艺术"},
        ],
        "local_food": ["北京烤鸭", "炸酱面", "豆汁儿", "涮羊肉", "卤煮"],
        "tips": "故宫需提前预约；长城建议避开节假日；地铁很方便",
    },
    "上海": {
        "name_en": "Shanghai",
        "region": "华东",
        "best_season": "3-5月, 9-11月",
        "features": ["现代化", "外滩", "迪士尼", "购物", "美食"],
        "avg_cost_per_day": {
            "经济": 350,
            "舒适": 700,
            "豪华": 1500,
        },
        "attractions": [
            {"name": "外滩", "time": "2小时", "ticket": 0, "type": "地标"},
            {"name": "东方明珠", "time": "2小时", "ticket": 199, "type": "地标"},
            {"name": "上海迪士尼", "time": "一天", "ticket": 475, "type": "乐园"},
            {"name": "豫园", "time": "2小时", "ticket": 30, "type": "园林"},
            {"name": "南京路步行街", "time": "2小时", "ticket": 0, "type": "逛街"},
            {"name": "武康路", "time": "2小时", "ticket": 0, "type": "文艺"},
        ],
        "local_food": ["小笼包", "生煎包", "蟹壳黄", "葱油拌面", "八宝饭"],
        "tips": "迪士尼建议工作日去；地铁覆盖全城；外滩夜景最美",
    },
    "成都": {
        "name_en": "Chengdu",
        "region": "西南",
        "best_season": "3-6月, 9-11月",
        "features": ["美食", "大熊猫", "火锅", "慢生活", "文化"],
        "avg_cost_per_day": {
            "经济": 250,
            "舒适": 500,
            "豪华": 1000,
        },
        "attractions": [
            {"name": "大熊猫繁育基地", "time": "半天", "ticket": 55, "type": "动物"},
            {"name": "宽窄巷子", "time": "2小时", "ticket": 0, "type": "文化"},
            {"name": "锦里", "time": "2小时", "ticket": 0, "type": "逛街"},
            {"name": "武侯祠", "time": "2小时", "ticket": 50, "type": "历史"},
            {"name": "都江堰", "time": "半天", "ticket": 80, "type": "历史"},
            {"name": "青城山", "time": "一天", "ticket": 90, "type": "自然"},
        ],
        "local_food": ["火锅", "串串香", "担担面", "龙抄手", "兔头"],
        "tips": "熊猫基地早上去熊猫最活跃；火锅必吃；春熙路很热闹",
    },
    "西安": {
        "name_en": "Xi'an",
        "region": "西北",
        "best_season": "3-5月, 9-11月",
        "features": ["古都", "兵马俑", "历史", "美食", "城墙"],
        "avg_cost_per_day": {
            "经济": 250,
            "舒适": 500,
            "豪华": 1000,
        },
        "attractions": [
            {"name": "兵马俑", "time": "半天", "ticket": 120, "type": "历史"},
            {"name": "西安城墙", "time": "2-3小时", "ticket": 54, "type": "历史"},
            {"name": "大雁塔", "time": "2小时", "ticket": 40, "type": "历史"},
            {"name": "回民街", "time": "2小时", "ticket": 0, "type": "美食"},
            {"name": "陕西历史博物馆", "time": "半天", "ticket": 0, "type": "历史"},
            {"name": "华清宫", "time": "半天", "ticket": 120, "type": "历史"},
        ],
        "local_food": ["肉夹馍", "凉皮", "羊肉泡馍", "BiangBiang面", "甑糕"],
        "tips": "兵马俑在城外需半天；陕博免费需提前约；城墙可以骑自行车",
    },
    "杭州": {
        "name_en": "Hangzhou",
        "region": "华东",
        "best_season": "3-5月, 9-10月",
        "features": ["西湖", "江南水乡", "茶文化", "园林"],
        "avg_cost_per_day": {
            "经济": 300,
            "舒适": 600,
            "豪华": 1200,
        },
        "attractions": [
            {"name": "西湖", "time": "一天", "ticket": 0, "type": "自然"},
            {"name": "灵隐寺", "time": "半天", "ticket": 75, "type": "宗教"},
            {"name": "宋城", "time": "半天", "ticket": 300, "type": "文化"},
            {"name": "西溪湿地", "time": "半天", "ticket": 80, "type": "自然"},
            {"name": "龙井村", "time": "2小时", "ticket": 0, "type": "茶文化"},
        ],
        "local_food": ["西湖醋鱼", "东坡肉", "龙井虾仁", "叫花鸡", "葱包烩"],
        "tips": "西湖可免费游览；龙井村可品茶；西湖骑行很棒",
    },
    "昆明": {
        "name_en": "Kunming",
        "region": "西南",
        "best_season": "3-10月",
        "features": ["春城", "花海", "少数民族", "气候宜人"],
        "avg_cost_per_day": {
            "经济": 200,
            "舒适": 400,
            "豪华": 800,
        },
        "attractions": [
            {"name": "石林", "time": "一天", "ticket": 130, "type": "自然"},
            {"name": "滇池", "time": "半天", "ticket": 0, "type": "自然"},
            {"name": "云南民族村", "time": "半天", "ticket": 90, "type": "文化"},
            {"name": "翠湖公园", "time": "2小时", "ticket": 0, "type": "休闲"},
            {"name": "斗南花市", "time": "2小时", "ticket": 0, "type": "购物"},
        ],
        "local_food": ["过桥米线", "汽锅鸡", "野生菌火锅", "烤乳扇", "鲜花饼"],
        "tips": "昆明是去大理丽江的中转站；斗南花市亚洲最大",
    },
    "三亚": {
        "name_en": "Sanya",
        "region": "华南",
        "best_season": "10-4月",
        "features": ["海滩", "度假", "潜水", "热带风光"],
        "avg_cost_per_day": {
            "经济": 300,
            "舒适": 700,
            "豪华": 1500,
        },
        "attractions": [
            {"name": "亚龙湾", "time": "半天", "ticket": 0, "type": "海滩"},
            {"name": "蜈支洲岛", "time": "一天", "ticket": 140, "type": "海岛"},
            {"name": "天涯海角", "time": "2-3小时", "ticket": 81, "type": "地标"},
            {"name": "南山寺", "time": "半天", "ticket": 108, "type": "宗教"},
            {"name": "热带天堂森林公园", "time": "半天", "ticket": 150, "type": "自然"},
        ],
        "local_food": ["海鲜", "椰子鸡", "抱罗粉", "清补凉"],
        "tips": "10月-4月最佳；亚龙湾沙质最好；海鲜去第一市场",
    },
    "重庆": {
        "name_en": "Chongqing",
        "region": "西南",
        "best_season": "3-5月, 9-11月",
        "features": ["山城", "火锅", "夜景", "魔幻交通"],
        "avg_cost_per_day": {
            "经济": 250,
            "舒适": 500,
            "豪华": 1000,
        },
        "attractions": [
            {"name": "洪崖洞", "time": "2小时", "ticket": 0, "type": "地标"},
            {"name": "磁器口古镇", "time": "2-3小时", "ticket": 0, "type": "文化"},
            {"name": "长江索道", "time": "1小时", "ticket": 20, "type": "体验"},
            {"name": "武隆天生三桥", "time": "一天", "ticket": 125, "type": "自然"},
            {"name": "解放碑", "time": "1小时", "ticket": 0, "type": "地标"},
        ],
        "local_food": ["重庆火锅", "小面", "酸辣粉", "烤鱼", "毛血旺"],
        "tips": "导航可能不准（立体城市）；火锅微辣也很辣；夜景必看",
    },
    "大理": {
        "name_en": "Dali",
        "region": "西南",
        "best_season": "3-5月, 9-11月",
        "features": ["古城", "洱海", "苍山", "文艺", "慢生活"],
        "avg_cost_per_day": {
            "经济": 200,
            "舒适": 400,
            "豪华": 800,
        },
        "attractions": [
            {"name": "洱海", "time": "一天", "ticket": 0, "type": "自然"},
            {"name": "大理古城", "time": "半天", "ticket": 0, "type": "文化"},
            {"name": "苍山", "time": "半天", "ticket": 40, "type": "自然"},
            {"name": "崇圣寺三塔", "time": "2小时", "ticket": 75, "type": "宗教"},
            {"name": "喜洲古镇", "time": "2小时", "ticket": 0, "type": "文化"},
        ],
        "local_food": ["乳扇", "大理砂锅鱼", "凉鸡米线", "雕梅"],
        "tips": "洱海建议租车环湖骑行；古城适合发呆；早晚温差大",
    },
    "广州": {
        "name_en": "Guangzhou",
        "region": "华南",
        "best_season": "10-12月, 3-4月",
        "features": ["美食", "购物", "历史", "现代都市"],
        "avg_cost_per_day": {
            "经济": 300,
            "舒适": 600,
            "豪华": 1200,
        },
        "attractions": [
            {"name": "广州塔", "time": "2小时", "ticket": 150, "type": "地标"},
            {"name": "长隆野生动物世界", "time": "一天", "ticket": 300, "type": "乐园"},
            {"name": "沙面", "time": "2小时", "ticket": 0, "type": "文艺"},
            {"name": "北京路步行街", "time": "2小时", "ticket": 0, "type": "逛街"},
            {"name": "陈家祠", "time": "1-2小时", "ticket": 10, "type": "历史"},
            {"name": "白云山", "time": "半天", "ticket": 5, "type": "自然"},
        ],
        "local_food": ["白切鸡", "肠粉", "煲仔饭", "云吞面", "双皮奶", "烧鹅"],
        "tips": "早茶是广州灵魂；地铁很方便；上下九步行街很有烟火气",
    },
    "厦门": {
        "name_en": "Xiamen",
        "region": "华东",
        "best_season": "3-5月, 10-12月",
        "features": ["海岛", "文艺", "浪漫", "美食"],
        "avg_cost_per_day": {
            "经济": 250,
            "舒适": 500,
            "豪华": 1100,
        },
        "attractions": [
            {"name": "鼓浪屿", "time": "一天", "ticket": 0, "type": "海岛"},
            {"name": "厦门大学", "time": "2小时", "ticket": 0, "type": "校园"},
            {"name": "曾厝垵", "time": "2小时", "ticket": 0, "type": "文艺"},
            {"name": "环岛路", "time": "2小时", "ticket": 0, "type": "自然"},
            {"name": "南普陀寺", "time": "1-2小时", "ticket": 0, "type": "宗教"},
            {"name": "中山路步行街", "time": "2小时", "ticket": 0, "type": "逛街"},
        ],
        "local_food": ["沙茶面", "土笋冻", "海蛎煎", "姜母鸭", "花生汤"],
        "tips": "鼓浪屿船票提前约；厦大需预约入校；环岛路骑行很棒",
    },
    "南京": {
        "name_en": "Nanjing",
        "region": "华东",
        "best_season": "3-5月, 9-11月",
        "features": ["六朝古都", "历史", "梧桐", "美食"],
        "avg_cost_per_day": {
            "经济": 280,
            "舒适": 550,
            "豪华": 1100,
        },
        "attractions": [
            {"name": "夫子庙-秦淮河", "time": "半天", "ticket": 0, "type": "历史"},
            {"name": "中山陵", "time": "半天", "ticket": 0, "type": "历史"},
            {"name": "南京博物院", "time": "半天", "ticket": 0, "type": "文化"},
            {"name": "明孝陵", "time": "2-3小时", "ticket": 70, "type": "历史"},
            {"name": "玄武湖", "time": "2小时", "ticket": 0, "type": "自然"},
            {"name": "鸡鸣寺", "time": "1-2小时", "ticket": 10, "type": "宗教"},
        ],
        "local_food": ["鸭血粉丝汤", "盐水鸭", "小笼包", "桂花糖芋苗", "牛肉锅贴"],
        "tips": "夫子庙夜景最美；博物院免费需预约；秋天梧桐大道很美",
    },
    "武汉": {
        "name_en": "Wuhan",
        "region": "华中",
        "best_season": "3-5月, 9-11月",
        "features": ["江城", "樱花", "美食", "历史"],
        "avg_cost_per_day": {
            "经济": 250,
            "舒适": 500,
            "豪华": 1000,
        },
        "attractions": [
            {"name": "黄鹤楼", "time": "2小时", "ticket": 70, "type": "历史"},
            {"name": "武汉大学", "time": "2小时", "ticket": 0, "type": "校园"},
            {"name": "东湖风景区", "time": "半天", "ticket": 0, "type": "自然"},
            {"name": "户部巷", "time": "1-2小时", "ticket": 0, "type": "美食"},
            {"name": "江汉路步行街", "time": "2小时", "ticket": 0, "type": "逛街"},
            {"name": "湖北省博物馆", "time": "半天", "ticket": 0, "type": "文化"},
        ],
        "local_food": ["热干面", "武汉鸭脖", "豆皮", "面窝", "排骨藕汤"],
        "tips": "武大樱花季人极多需预约；东湖比西湖大很多；户部巷偏游客",
    },
    "长沙": {
        "name_en": "Changsha",
        "region": "华中",
        "best_season": "3-5月, 9-11月",
        "features": ["美食", "娱乐", "历史", "夜生活"],
        "avg_cost_per_day": {
            "经济": 250,
            "舒适": 500,
            "豪华": 1000,
        },
        "attractions": [
            {"name": "岳麓山", "time": "半天", "ticket": 0, "type": "自然"},
            {"name": "橘子洲", "time": "2-3小时", "ticket": 0, "type": "地标"},
            {"name": "太平老街", "time": "2小时", "ticket": 0, "type": "美食"},
            {"name": "湖南省博物馆", "time": "半天", "ticket": 0, "type": "文化"},
            {"name": "坡子街", "time": "1-2小时", "ticket": 0, "type": "美食"},
            {"name": "梅溪湖", "time": "2小时", "ticket": 0, "type": "文艺"},
        ],
        "local_food": ["臭豆腐", "小龙虾", "茶颜悦色", "糖油粑粑", "米粉", "剁椒鱼头"],
        "tips": "茶颜悦色只有长沙有；橘子洲周末有烟花；博物馆看辛追夫人",
    },
    "青岛": {
        "name_en": "Qingdao",
        "region": "华东",
        "best_season": "5-10月",
        "features": ["海滨", "啤酒", "欧式建筑", "海鲜"],
        "avg_cost_per_day": {
            "经济": 280,
            "舒适": 550,
            "豪华": 1200,
        },
        "attractions": [
            {"name": "栈桥", "time": "1小时", "ticket": 0, "type": "地标"},
            {"name": "八大关", "time": "半天", "ticket": 0, "type": "文艺"},
            {"name": "崂山", "time": "一天", "ticket": 80, "type": "自然"},
            {"name": "青岛啤酒博物馆", "time": "2小时", "ticket": 60, "type": "文化"},
            {"name": "五四广场", "time": "1小时", "ticket": 0, "type": "地标"},
            {"name": "金沙滩", "time": "半天", "ticket": 0, "type": "海滩"},
        ],
        "local_food": ["海鲜", "青岛啤酒", "鲅鱼水饺", "辣炒蛤蜊", "烤鱿鱼"],
        "tips": "8月啤酒节最热闹；崂山建议一天；海鲜去市场买加工最划算",
    },
    "桂林": {
        "name_en": "Guilin",
        "region": "华南",
        "best_season": "4-10月",
        "features": ["山水", "喀斯特", "漓江", "田园"],
        "avg_cost_per_day": {
            "经济": 200,
            "舒适": 400,
            "豪华": 800,
        },
        "attractions": [
            {"name": "漓江", "time": "一天", "ticket": 0, "type": "自然"},
            {"name": "阳朔西街", "time": "半天", "ticket": 0, "type": "文艺"},
            {"name": "十里画廊", "time": "半天", "ticket": 0, "type": "自然"},
            {"name": "象鼻山", "time": "1-2小时", "ticket": 55, "type": "地标"},
            {"name": "龙脊梯田", "time": "一天", "ticket": 80, "type": "自然"},
            {"name": "银子岩", "time": "2小时", "ticket": 80, "type": "自然"},
        ],
        "local_food": ["桂林米粉", "啤酒鱼", "田螺酿", "漓江虾", "桂花糕"],
        "tips": "阳朔是精华；漓江竹筏推荐杨堤-兴坪段；龙脊梯田秋季最美",
    },
    "丽江": {
        "name_en": "Lijiang",
        "region": "西南",
        "best_season": "3-5月, 9-11月",
        "features": ["古城", "雪山", "纳西文化", "文艺"],
        "avg_cost_per_day": {
            "经济": 220,
            "舒适": 450,
            "豪华": 900,
        },
        "attractions": [
            {"name": "丽江古城", "time": "一天", "ticket": 0, "type": "文化"},
            {"name": "玉龙雪山", "time": "一天", "ticket": 100, "type": "自然"},
            {"name": "泸沽湖", "time": "1-2天", "ticket": 70, "type": "自然"},
            {"name": "束河古镇", "time": "半天", "ticket": 0, "type": "文化"},
            {"name": "虎跳峡", "time": "半天", "ticket": 45, "type": "自然"},
            {"name": "拉市海", "time": "半天", "ticket": 0, "type": "自然"},
        ],
        "local_food": ["腊排骨火锅", "过桥米线", "鸡豆凉粉", "酥油茶", "纳西烤鱼"],
        "tips": "古城石板路拖箱不便；玉龙雪山索道票需抢；泸沽湖建议住一晚",
    },
    "哈尔滨": {
        "name_en": "Harbin",
        "region": "东北",
        "best_season": "12-2月, 6-8月",
        "features": ["冰雕", "俄式建筑", "滑雪", "冰雪"],
        "avg_cost_per_day": {
            "经济": 250,
            "舒适": 500,
            "豪华": 1000,
        },
        "attractions": [
            {"name": "冰雪大世界", "time": "半天", "ticket": 300, "type": "冰雪"},
            {"name": "中央大街", "time": "2小时", "ticket": 0, "type": "逛街"},
            {"name": "圣索菲亚教堂", "time": "1小时", "ticket": 0, "type": "地标"},
            {"name": "太阳岛", "time": "半天", "ticket": 30, "type": "自然"},
            {"name": "亚布力滑雪场", "time": "一天", "ticket": 200, "type": "冰雪"},
            {"name": "老道外", "time": "2小时", "ticket": 0, "type": "文化"},
        ],
        "local_food": ["锅包肉", "哈尔滨红肠", "马迭尔冰棍", "铁锅炖", "大列巴"],
        "tips": "冰雪大世界12月底才开放；冬天注意保暖(-30°C)；红肠买秋林牌的",
    },
    "苏州": {
        "name_en": "Suzhou",
        "region": "华东",
        "best_season": "3-5月, 9-11月",
        "features": ["园林", "水乡", "古镇", "丝绸"],
        "avg_cost_per_day": {
            "经济": 280,
            "舒适": 550,
            "豪华": 1100,
        },
        "attractions": [
            {"name": "拙政园", "time": "2-3小时", "ticket": 80, "type": "园林"},
            {"name": "平江路", "time": "2小时", "ticket": 0, "type": "文艺"},
            {"name": "虎丘", "time": "半天", "ticket": 70, "type": "历史"},
            {"name": "周庄古镇", "time": "半天", "ticket": 100, "type": "古镇"},
            {"name": "苏州博物馆", "time": "2小时", "ticket": 0, "type": "文化"},
            {"name": "山塘街", "time": "2小时", "ticket": 0, "type": "水乡"},
        ],
        "local_food": ["松鼠桂鱼", "阳澄湖大闸蟹", "苏式汤面", "桂花糕", "碧螺春"],
        "tips": "苏博由贝聿铭设计需预约；拙政园早上人少；平江路比山塘街更文艺",
    },
    "洛阳": {
        "name_en": "Luoyang",
        "region": "华中",
        "best_season": "4-5月, 9-10月",
        "features": ["古都", "牡丹", "石窟", "历史"],
        "avg_cost_per_day": {
            "经济": 200,
            "舒适": 400,
            "豪华": 800,
        },
        "attractions": [
            {"name": "龙门石窟", "time": "半天", "ticket": 90, "type": "历史"},
            {"name": "白马寺", "time": "2小时", "ticket": 35, "type": "宗教"},
            {"name": "洛阳博物馆", "time": "半天", "ticket": 0, "type": "文化"},
            {"name": "老君山", "time": "一天", "ticket": 100, "type": "自然"},
            {"name": "应天门", "time": "1-2小时", "ticket": 30, "type": "历史"},
            {"name": "洛邑古城", "time": "2小时", "ticket": 0, "type": "文化"},
        ],
        "local_food": ["洛阳水席", "牛肉汤", "羊肉汤", "牡丹饼", "浆面条"],
        "tips": "4月牡丹花会最值得去；龙门石窟建议请讲解；老君山冬季有雪景",
    },
    "贵阳": {
        "name_en": "Guiyang",
        "region": "西南",
        "best_season": "6-9月",
        "features": ["避暑", "山水", "美食", "民族风情"],
        "avg_cost_per_day": {
            "经济": 200,
            "舒适": 400,
            "豪华": 800,
        },
        "attractions": [
            {"name": "黄果树瀑布", "time": "半天", "ticket": 160, "type": "自然"},
            {"name": "黔灵山公园", "time": "半天", "ticket": 5, "type": "自然"},
            {"name": "青岩古镇", "time": "半天", "ticket": 10, "type": "古镇"},
            {"name": "甲秀楼", "time": "1小时", "ticket": 0, "type": "地标"},
            {"name": "荔波小七孔", "time": "一天", "ticket": 130, "type": "自然"},
            {"name": "肇兴侗寨", "time": "半天", "ticket": 80, "type": "文化"},
        ],
        "local_food": ["酸汤鱼", "花溪牛肉粉", "肠旺面", "丝娃娃", "折耳根"],
        "tips": "夏季平均25°C是绝佳避暑地；黄果树瀑布雨季最壮观；酸汤鱼必吃",
    },
    "张家界": {
        "name_en": "Zhangjiajie",
        "region": "华中",
        "best_season": "4-6月, 9-10月",
        "features": ["石英砂岩峰林", "玻璃栈道", "自然奇观", "阿凡达"],
        "avg_cost_per_day": {
            "经济": 220,
            "舒适": 450,
            "豪华": 900,
        },
        "attractions": [
            {"name": "张家界国家森林公园", "time": "1-2天", "ticket": 228, "type": "自然"},
            {"name": "天门山", "time": "一天", "ticket": 258, "type": "自然"},
            {"name": "大峡谷玻璃桥", "time": "半天", "ticket": 118, "type": "体验"},
            {"name": "黄龙洞", "time": "2小时", "ticket": 100, "type": "自然"},
            {"name": "宝峰湖", "time": "2小时", "ticket": 96, "type": "自然"},
            {"name": "凤凰古城", "time": "一天", "ticket": 0, "type": "古镇"},
        ],
        "local_food": ["三下锅", "土家腊肉", "血豆腐", "葛根粉", "米豆腐"],
        "tips": "森林公园至少一天半；天门山索道是世界最长；玻璃桥建议早上去",
    },
    "拉萨": {
        "name_en": "Lhasa",
        "region": "西南",
        "best_season": "6-9月",
        "features": ["藏传佛教", "高原", "布达拉宫", "藏族文化"],
        "avg_cost_per_day": {
            "经济": 250,
            "舒适": 500,
            "豪华": 1000,
        },
        "attractions": [
            {"name": "布达拉宫", "time": "半天", "ticket": 200, "type": "历史"},
            {"name": "大昭寺", "time": "2小时", "ticket": 85, "type": "宗教"},
            {"name": "八廓街", "time": "2小时", "ticket": 0, "type": "逛街"},
            {"name": "纳木错", "time": "一天", "ticket": 120, "type": "自然"},
            {"name": "色拉寺", "time": "2小时", "ticket": 50, "type": "宗教"},
            {"name": "羊卓雍措", "time": "半天", "ticket": 60, "type": "自然"},
        ],
        "local_food": ["酥油茶", "甜茶", "藏面", "糌粑", "牦牛肉干"],
        "tips": "布宫需提前一天预约；注意高反建议先在林芝过渡；进寺庙要脱帽",
    },
}

# 默认汇率（相对于人民币）
CURRENCY_RATES = {
    "CNY": 1.0,
    "USD": 7.2,
    "EUR": 7.8,
    "JPY": 0.05,
    "KRW": 0.0055,
    "THB": 0.20,
    "GBP": 9.1,
    "AUD": 4.8,
    "HKD": 0.92,
    "TWD": 0.23,
}


def search_cities(keyword: str) -> list[str]:
    """根据关键词搜索城市"""
    keyword = keyword.lower()
    matches = []
    for name, info in CITIES.items():
        if keyword in name.lower() or keyword in info.get("name_en", "").lower():
            matches.append(name)
        elif keyword in info.get("region", "").lower():
            matches.append(name)
    return matches


def get_city(name: str) -> dict | None:
    """获取城市信息"""
    return CITIES.get(name)


def get_attractions(city: str) -> list[dict]:
    """获取城市景点列表"""
    info = CITIES.get(city)
    return info["attractions"] if info else []


def estimate_daily_cost(city: str, style: str = "舒适") -> int:
    """估算每日花费（元/人）"""
    info = CITIES.get(city)
    if not info:
        return 400  # 默认值
    costs = info["avg_cost_per_day"]
    return costs.get(style, costs.get("舒适", 400))


def get_all_cities() -> list[str]:
    """获取所有城市列表"""
    return list(CITIES.keys())
