# app/api/routers/posts.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import Post, User
from app.schemas import PostCreate, PostUpdate, PostResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[PostResponse])
def read_posts(
    skip: int = 0, 
    limit: int = 50, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # 获取当前用户
):
    query = db.query(Post)
    
    # 管理员看全部，普通用户只看 active
    if current_user.username != "admin":
        query = query.filter(Post.status == "active")
        
    posts = query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
    return posts

@router.post("/", response_model=PostResponse)
def create_post(
    post_in: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 如果带有 parent_id (即 Fork 操作)，需要验证原贴是否存在
    if post_in.parent_id:
        parent = db.query(Post).filter(Post.id == post_in.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="源帖子不存在")
            
    new_post = Post(
        title=post_in.title,
        content=post_in.content,
        author_id=current_user.id,
        parent_id=post_in.parent_id,
        created_via="web" # 后续 CLI 可在请求体或 header 中覆盖
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@router.get("/{post_id}", response_model=PostResponse)
def read_post(
    post_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # 获取当前用户
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子未找到")
        
    # 如果是已删除贴且访问者不是 admin，则抛出 410
    if post.status == "deleted" and current_user.username != "admin":
        raise HTTPException(status_code=410, detail="该内容已被原作者移除")
        
    return post

@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: str,
    post_in: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post or post.status == "deleted":
        raise HTTPException(status_code=404, detail="帖子未找到或已删除")
    
    # 权限校验：只能修改自己的帖子
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改他人的帖子")
        
    if post_in.title is not None: post.title = post_in.title
    if post_in.content is not None: post.content = post_in.content
    
    db.commit()
    db.refresh(post)
    return post

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post or post.status == "deleted":
        raise HTTPException(status_code=404, detail="帖子未找到")
        
    # 只有作者或管理员可以删除
    if post.author_id != current_user.id and current_user.username != "admin":
        raise HTTPException(status_code=403, detail="无权删除他人的帖子")
        
    post.status = "deleted"
    db.commit()
    return None