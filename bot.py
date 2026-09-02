import os,io,random,sqlite3,asyncio
from pathlib import Path
import discord
from discord.ext import commands
from PIL import Image,ImageDraw,ImageFont
TOKEN=os.getenv('DISCORD_BOT_TOKEN'); ROOT=Path(__file__).parent; DB=ROOT/'surfboard.db'; IMG=ROOT/'purple_surfboard_base.png'; ALLOWED_CHANNEL_ID = 1544573699397656677

def ft(n):
 for p in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
  if Path(p).exists(): return ImageFont.truetype(p,n)
 return ImageFont.load_default()
F1,F2,F3=ft(48),ft(38),ft(28)
def con():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute('CREATE TABLE IF NOT EXISTS items(user_id INTEGER PRIMARY KEY,base_atk INTEGER,base_speed INTEGER,atk INTEGER,str_stat INTEGER,pdef INTEGER,speed INTEGER,slots INTEGER,used INTEGER,destroyed INTEGER)'); c.commit(); return c
def new(uid):
 a=random.randint(99,104); s=random.randint(5,6); c=con(); c.execute('DELETE FROM items WHERE user_id=?',(uid,)); c.execute('INSERT INTO items VALUES(?,?,?,?,?,?,?,?,?,?)',(uid,a,s,a,0,0,s,7,0,0)); c.commit(); r=dict(c.execute('SELECT * FROM items WHERE user_id=?',(uid,)).fetchone()); c.close(); return r
def get(uid):
 c=con(); r=c.execute('SELECT * FROM items WHERE user_id=?',(uid,)).fetchone(); c.close(); return dict(r) if r else new(uid)
def save(x):
 c=con(); c.execute('UPDATE items SET atk=?,str_stat=?,pdef=?,slots=?,used=?,destroyed=? WHERE user_id=?',(x['atk'],x['str_stat'],x['pdef'],x['slots'],x['used'],x['destroyed'],x['user_id'])); c.commit(); c.close()
def allowed(i):
 if not ALLOWED_CHANNEL_ID:return True
 ch=i.channel; return bool(ch and (ch.id==ALLOWED_CHANNEL_ID or getattr(ch,'parent_id',None)==ALLOWED_CHANNEL_ID))
def color(x):
 b=(x['atk']-x['base_atk'])+x['str_stat']+x['pdef']
 if x['used']==0:return '흰색',(245,245,245)
 if b<=5:return '주황색',(255,165,50)
 if b<=22:return '파란색',(80,160,255)
 if b<=39:return '보라색',(190,100,255)
 if b<=56:return '노란색',(255,225,60)
 if b<=73:return '초록색',(80,230,100)
 return '빨간색',(255,80,80)
def normal(x,chance,atk,st=0,pdef=0,boom=0):
 if x['destroyed']:return 'destroyed'
 if x['slots']<=0:return 'no_slots'
 x['slots']-=1;x['used']+=1
 if random.random()<chance:x['atk']+=atk;x['str_stat']+=st;x['pdef']+=pdef;save(x);return 'success'
 if boom and random.random()<boom:x['destroyed']=1;save(x);return 'boom'
 save(x);return 'fail'
def white(x,chance,boom):
 if x['destroyed']:return 'destroyed'
 if x['slots']>=7:return 'full_slots'
 if random.random()<chance:x['slots']+=1;save(x);return 'success'
 if random.random()<boom:x['destroyed']=1;save(x);return 'boom'
 save(x);return 'fail'
def render(x):
 im=Image.new('RGB',(1200,900),(3,18,48));d=ImageDraw.Draw(im);cn,cc=color(x);d.text((600,25),'보라색 서핑보드',font=F1,fill=cc,anchor='ma');d.text((600,85),f'아이템 이름 색상 : {cn}',font=F3,fill=cc,anchor='ma')
 src=Image.open(IMG).convert('RGB'); icon=src.crop((0,35,105,185)).resize((260,370),Image.Resampling.NEAREST); im.paste(icon,(55,145))
 if x['destroyed']:d.text((720,290),'아이템 파괴',font=F1,fill=(255,80,80),anchor='mm')
 else:
  for j,t in enumerate([f"공격력 : +{x['atk']} (기본 {x['base_atk']})",f"STR : +{x['str_stat']}",f"물리방어력 : +{x['pdef']}",f"이동속도 : +{x['speed']}",f"남은 업횟 : {x['slots']} / 7"]):d.text((380,160+j*65),t,font=F2,fill='white')
 rules=['폴공 30% : 공격력 +5 / STR +3 / 물리방어력 +1','실패 시 50% 확률 아이템 파괴','폴공 60% : 공격력 +2 / STR +1','폴공 100% : 공격력 +1','백의 1% : 성공 업횟 +1 / 실패 시 2% 파괴','백의 3% : 성공 업횟 +1 / 실패 시 6% 파괴']
 for j,t in enumerate(rules):d.text((55,590+j*44),t,font=F3,fill='white')
 b=io.BytesIO();im.save(b,'JPEG',quality=92);b.seek(0);return b
def emb(x,title='보라색 서핑보드 강화'):
 _,c=color(x);e=discord.Embed(title=title,color=discord.Color.from_rgb(*c));e.set_image(url='attachment://surfboard.jpg');return e
class V(discord.ui.View):
 def __init__(self,uid):super().__init__(timeout=None);self.uid=uid
 async def go(self,i,k):
  if i.user.id!=self.uid:return await i.response.send_message('❌ 본인의 장비만 강화할 수 있습니다.',ephemeral=True)
  await i.response.defer();x=get(i.user.id)
  if k=='30':r=normal(x,.30,5,3,1,.50);lab='폴공 30%'
  elif k=='60':r=normal(x,.60,2,1);lab='폴공 60%'
  elif k=='100':r=normal(x,1,1);lab='폴공 100%'
  elif k=='w1':r=white(x,.01,.02);lab='백의 1%'
  else:r=white(x,.03,.06);lab='백의 3%'
  x=get(i.user.id);titles={'success':f'✨ {lab} 성공!','fail':f'💨 {lab} 실패','boom':f'💥 {lab} 실패 — 아이템 파괴!','destroyed':'💥 이미 파괴된 아이템입니다.','no_slots':'❌ 남은 업횟이 없습니다.','full_slots':'❌ 복구할 업횟이 없습니다.'};pic=await asyncio.to_thread(render,x);await i.edit_original_response(embed=emb(x,titles[r]),attachments=[discord.File(pic,filename='surfboard.jpg')],view=V(i.user.id))
 @discord.ui.button(label='⚔️ 폴공 30%',style=discord.ButtonStyle.danger,row=0)
 async def a(self,i,b):await self.go(i,'30')
 @discord.ui.button(label='⚔️ 폴공 60%',style=discord.ButtonStyle.primary,row=0)
 async def b(self,i,b):await self.go(i,'60')
 @discord.ui.button(label='⚔️ 폴공 100%',style=discord.ButtonStyle.secondary,row=0)
 async def c(self,i,b):await self.go(i,'100')
 @discord.ui.button(label='📜 백의 1%',style=discord.ButtonStyle.secondary,row=1)
 async def d(self,i,b):await self.go(i,'w1')
 @discord.ui.button(label='📜 백의 3%',style=discord.ButtonStyle.secondary,row=1)
 async def e(self,i,b):await self.go(i,'w3')
 @discord.ui.button(label='🔄 초기화',style=discord.ButtonStyle.danger,row=2)
 async def f(self,i,b):
  if i.user.id!=self.uid:return await i.response.send_message('❌ 본인의 장비만 초기화할 수 있습니다.',ephemeral=True)
  await i.response.defer();x=new(i.user.id);pic=await asyncio.to_thread(render,x);await i.edit_original_response(embed=emb(x,'🔄 새 서핑보드 생성'),attachments=[discord.File(pic,filename='surfboard.jpg')],view=V(i.user.id))
bot=commands.Bot(command_prefix='!',intents=discord.Intents.default())
GUILD_ID = 1536042800754466906

@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)
    print(f"로그인 완료: {bot.user} / 서버 명령어 {len(synced)}개 동기화 완료")

@bot.tree.command(name='보핑강화',description='보라색 서핑보드 강화 시뮬레이션')
async def cmd(i:discord.Interaction):
 if not allowed(i):return await i.response.send_message('❌ 이 게시판에서는 사용할 수 없습니다.',ephemeral=True)
 await i.response.defer();x=get(i.user.id);pic=await asyncio.to_thread(render,x);await i.edit_original_response(embed=emb(x),attachments=[discord.File(pic,filename='surfboard.jpg')],view=V(i.user.id))
@bot.tree.command(name='보핑초기화',description='새 보라색 서핑보드를 뽑습니다')
async def rst(i:discord.Interaction):
 x=new(i.user.id);await i.response.send_message(f"🔄 새 보드: 공격력 {x['atk']} / 이동속도 {x['speed']}",ephemeral=True)

@bot.tree.command(name="보핑랭킹", description="보라색 서핑보드 강화 랭킹")
async def surfboard_rank(i:discord.Interaction):
    if not allowed(i):
        return await i.response.send_message("❌ 이 게시판에서는 사용할 수 없습니다.", ephemeral=True)

    con = connect()
    rows = con.execute("SELECT * FROM items WHERE destroyed=0").fetchall()
    con.close()

    ranked = []
    for r in rows:
        x = dict(r)
        grade = x["atk"] + (x["str_stat"] * 0.2)
        ranked.append((grade, x["atk"], x["str_stat"], x["user_id"]))

    ranked.sort(key=lambda v: (v[0], v[1], v[2]), reverse=True)

    if not ranked:
        return await i.response.send_message("아직 랭킹 기록이 없습니다.")

    lines = []
    for n, (grade, atk, strength, uid) in enumerate(ranked[:10], 1):
        lines.append(
            f"**{n}위** <@{uid}> — **{grade:.1f}급** "
            f"(공격력 {atk} / STR +{strength})"
        )

    await i.response.send_message("🏄 **보라색 서핑보드 TOP 10**\n\n" + "\n".join(lines))

if not TOKEN:raise RuntimeError('DISCORD_BOT_TOKEN을 설정해주세요.')
bot.run(TOKEN)
