# add_user.py
import sys
import uuid
import getpass
from app.db.database import SessionLocal
from app.db.models import User
from app.core.security import get_password_hash

def main():
    print("=== Snip Share 用户添加工具 ===")
    
    # 1. 获取用户名
    username = input("请输入新用户的用户名: ").strip()
    if not username:
        print("错误: 用户名不能为空。")
        sys.exit(1)
        
    db = SessionLocal()
    
    # 2. 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        print(f"错误: 用户名 '{username}' 已存在。")
        db.close()
        sys.exit(1)
        
    # 3. 交互式获取密码
    while True:
        password = getpass.getpass(f"请输入 {username} 的密码: ")
        confirm_password = getpass.getpass("请再次输入以确认: ")
        
        if len(password) < 6:
            print("提示: 密码长度建议至少6位。\n")
        if password != confirm_password:
            print("错误: 两次输入的密码不一致，请重试。\n")
            continue
        break
        
    # 4. 创建用户
    api_token = "tok_" + uuid.uuid4().hex
    
    new_user = User(
        username=username,
        password_hash=get_password_hash(password),
        api_token=api_token
    )
    
    try:
        db.add(new_user)
        db.commit()
        print("\n用户创建成功！")
        print("------------------------")
        print(f"用户名:   {username}")
        print(f"API Token: {api_token}")
        print("------------------------")
        print("请将上述信息发送给该用户。")
    except Exception as e:
        db.rollback()
        print(f"\n创建失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()