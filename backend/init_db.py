# init_db.py
import uuid
import getpass
from app.db.database import SessionLocal, engine, Base
from app.db.models import User
from app.core.security import get_password_hash

def init():
    # 确保表结构已创建
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    admin_user = db.query(User).filter(User.username == "admin").first()
    if admin_user:
        print("管理员账号 'admin' 已存在，跳过初始化。")
        db.close()
        return

    print("=== Snip Share 系统初始化 ===")
    print("正在创建默认管理员账号: admin")
    
    # 交互式获取并确认密码
    while True:
        password = getpass.getpass("请输入管理员初始密码: ")
        confirm_password = getpass.getpass("请再次输入以确认: ")
        
        if not password:
            print("错误: 密码不能为空，请重试。\n")
            continue
        if password != confirm_password:
            print("错误: 两次输入的密码不一致，请重试。\n")
            continue
        break
    
    # 生成专属 API Token
    api_token = "tok_" + uuid.uuid4().hex
    
    user = User(
        username="admin",
        password_hash=get_password_hash(password),
        api_token=api_token
    )
    db.add(user)
    db.commit()
    
    print("\n管理员账号创建成功！")
    print("用户名: admin")
    print(f"CLI 专属 API Token: {api_token}")
    print("请妥善保管您的密码和 Token。")
    
    db.close()

if __name__ == "__main__":
    init()