# app/api/routers/posts.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import Post, User
from app.schemas import PostCreate, PostUpdate, PostResponse
from app.api.deps import get_current_user, is_admin

router = APIRouter()

@router.get("/", response_model=List[PostResponse])
def read_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    mine: bool = False,  # 仅返回当前用户自己的帖子（CLI 使用）
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # 获取当前用户
):
    query = db.query(Post)

    # 管理员看全部，普通用户只看 active
    if not is_admin(current_user):
        query = query.filter(Post.status == "active")

    if mine:
        query = query.filter(Post.author_id == current_user.id)

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
        tags=post_in.tags,
        author_id=current_user.id,
        parent_id=post_in.parent_id,
        created_via=post_in.created_via,
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
    if post.status == "deleted" and not is_admin(current_user):
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

    # 权限校验：只有作者或管理员可以修改
    if post.author_id != current_user.id and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="无权修改他人的帖子")

    if post_in.title is not None: post.title = post_in.title
    if post_in.content is not None: post.content = post_in.content

    # 注意：前端传来的 tags 即使是空数组 [] 也应该覆盖，表示清空所有标签
    if post_in.tags is not None:
        post.tags = post_in.tags

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
    if post.author_id != current_user.id and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="无权删除他人的帖子")

    post.status = "deleted"
    db.commit()
    return None
