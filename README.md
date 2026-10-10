# SchoolFlow ကျောင်းစီမံခန့်ခွဲမှုစနစ်

SchoolFlow သည် ကျောင်းသား၊ ဆရာ/ဆရာမနှင့် အက်မင်တို့အတွက် role အလိုက် သီးခြားလုပ်ဆောင်ခွင့်များပါဝင်သော Django ဝဘ်အက်ပလီကေးရှင်းဖြစ်သည်။ အသုံးပြုသူများသည် နေ့စဉ်လုပ်ငန်းများကို SchoolFlow ၏ ကိုယ်ပိုင်စာမျက်နှာများမှ တိုက်ရိုက်ဆောင်ရွက်နိုင်သည်။

## Details about the site
Website ပေါ်မှာ User sites အတွက် 3 sites ရှိပါတယ်.

 one for admin panel, one for teachers panel and one for students panel.

Register စာမျက်နှာမှ ဖန်တီးသောအကောင့်များသည် Student သို့မဟုတ် Teacher အကောင့်များသာဖြစ်ပြီး Admin dashboard ကို ဝင်ခွင့်မရှိပါ။ Admin အဖြစ် စမ်းသပ်ရန် 


`createsuperuser` ဖြင့် admin account ဖွင့်နိုင်သည်၊ ထို acc Username and password ဖြင် login ၀င် ပြီး admin panel ကို test နိုင်ပါတယ် 

Teacher နှင့် Student များ၏ Course၊ Assignment နှင့် Submission လုပ်ငန်းများကို app ထဲက dashboard များမှပင် စီမံနိုင်သည်။

(or)

login by using this admin demo acc -
Username - Admin
Password - 786dreampro@:


## CRUD လုပ်ဆောင်ချက်များ

 Role အလိုက် လုပ်ဆောင်နိုင်သည့်အရာများမှာ -

- **အက်မင်** - Teacher နှင့် Student အကောင့်များကို ဖန်တီး၊ ကြည့်ရှု၊ ပြင်ဆင်၊ ဖျက်နိုင်သည်။ စနစ်အနှံ့ Course၊ Assignment နှင့် Submission မှတ်တမ်းများကိုလည်း အက်မင် dashboard တွင် ကြည့်ရှုနိုင်သည်။

- **ဆရာ/ဆရာမ** - ကိုယ်ပိုင် Course နှင့် Assignment များကို ဖန်တီး၊ ကြည့်ရှု၊ ပြင်ဆင်၊ ဖျက်နိုင်သည်။ ကျောင်းသားတင်သွင်းသော Submission များကို စစ်ဆေးပြီး အမှတ်နှင့် Feedback ပေးနိုင်သည်။

- **ကျောင်းသား** - Course များကို ရှာဖွေ၊ စာရင်းသွင်း၊ ပြန်လည်ထွက်နိုင်သည်။ Assignment အဖြေကို တင်သွင်း၊ ပြင်ဆင်၊ ဖျက်နိုင်ပြီး ကိုယ်ပိုင်အမှတ်နှင့် Feedback ကို ကြည့်နိုင်သည်။ ထို့အပြင် ကိုယ်ပိုင် Study Note များကို ဖန်တီး၊ ကြည့်ရှု၊ ရှာဖွေ၊ ပြင်ဆင်၊ ဖျက်နိုင်သည်။

အသုံးပြုသူတစ်ဦးချင်းစီသည် မိမိပိုင် Submission နှင့် Study Note များကိုသာ စီမံနိုင်ပြီး ဆရာ/ဆရာမသည် မိမိဖန်တီးထားသော Course နှင့် Assignment များကိုသာ စီမံနိုင်သည်။

## how it should work

1. ကျောင်းသားက Course Catalog မှ သင်တန်းတစ်ခုကို ရွေးချယ်စာရင်းသွင်းသည်။
2. ဆရာ/ဆရာမက Course အတွက် Assignment များ ဖန်တီးသည်။
3. ကျောင်းသားက အဖြေတင်သွင်းပြီး လိုအပ်ပါက ပြန်လည်ပြင်ဆင်နိုင်သည်။
4. ဆရာ/ဆရာမက အဖြေကို စစ်ဆေး၍ အမှတ်နှင့် Feedback ပေးသည်။
5. ကျောင်းသားက Dashboard တွင် အမှတ်၊ Feedback နှင့် ကိုယ်ပိုင် Study Note များကို စီမံကြည့်ရှုသည်။

##


pip install -r requirements.txt


## requirements
- Django
- SQLite
- Pillow

