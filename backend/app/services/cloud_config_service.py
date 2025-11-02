import json
from sqlalchemy.orm import Session
from app.models.cloud_config import CloudConfig
from app.schemas.cloud_config import CloudConfigCreate
from app.utils.encryption import encrypt, decrypt


def create_cloud_config(db: Session, user_id: int, cloud_config: CloudConfigCreate):
    creds_json = json.dumps(cloud_config.credentials or {})
    encrypted = encrypt(creds_json)
    db_config = CloudConfig(user_id=user_id, provider=cloud_config.provider, region=cloud_config.region, credentials=encrypted)
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


def update_cloud_config(db: Session, config_id: int, update_data: dict):
    config = db.query(CloudConfig).filter(CloudConfig.id == config_id).first()
    if not config:
        return None
    for key, value in update_data.items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config


def upsert_cloud_config(db: Session, user_id: int, cloud_config: CloudConfigCreate):
    existing_config = db.query(CloudConfig).filter(CloudConfig.user_id == user_id, CloudConfig.account_name == cloud_config.account_name).first()
    creds_json = json.dumps(cloud_config.credentials or {})
    encrypted = encrypt(creds_json)

    if not existing_config:
        db_config = CloudConfig(
            user_id=user_id,
            provider=cloud_config.provider,
            region=cloud_config.region,
            account_name=cloud_config.account_name,
            credentials=encrypted
        )
        db.add(db_config)
    else:
        existing_config.provider = cloud_config.provider
        existing_config.account_name = cloud_config.account_name
        existing_config.region = cloud_config.region
        existing_config.credentials = encrypted
        db_config = existing_config

    db.commit()
    db.refresh(db_config)
    return db_config


def list_cloud_configs(db: Session, user_id: int):
    rows = db.query(CloudConfig).filter(CloudConfig.user_id == user_id).all()
    results = []
    for r in rows:
        creds = {}
        if r.credentials:
            try:
                creds = json.loads(decrypt(r.credentials))
            except Exception:
                creds = {}
        results.append({
            "id": r.id,
            "provider": r.provider,
            "region": r.region,
            "credentials": creds
        })
    return results


def get_configs_dict(db: Session, user_id: int):
    """
    Return dict provider -> credentials dict (decrypted)
    Useful for agent factory.
    """
    rows = db.query(CloudConfig).filter(CloudConfig.user_id == user_id).all()
    out = {}
    for r in rows:
        try:
            creds = json.loads(decrypt(r.credentials)) if r.credentials else {}
        except Exception:
            creds = {}
        out.setdefault(r.provider, []).append({
            "region": r.region,
            "credentials": creds
        })
    return out
