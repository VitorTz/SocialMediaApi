from abc import ABC, abstractmethod
from fastapi import UploadFile
import cloudinary
import cloudinary.uploader
import cloudinary.api
import cloudinary.exceptions
from src.env import getenv


class StorageResponse:
    
    def __init__(
            self, 
            success: bool, 
            content: dict[str, str] = {},
            exception: Exception = None,
            err_msg: str = ""
        ):
        self.__success = success
        self.__content = content
        self.__exception = exception
        self.__err_msg = err_msg
    
    @property
    def success(self) -> bool:
        return self.__success
    
    @property
    def content(self) -> dict[str, str]:
        return self.__content
    
    @property
    def exception(self) -> Exception:
        return self.__exception
    
    @property
    def err_msg(self) -> str:
        return self.__err_msg
    
    def __str__(self):
        return f"StorageResponse=(success={self.__success}, err_msg{self.__err_msg}, exception={self.__exception}, content={self.__content})"


class Storage(ABC):

    @abstractmethod
    def __init__(self):
        self.open()

    @abstractmethod
    def open(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def create_user_folder(self, user_id: int) -> StorageResponse:
        pass

    @abstractmethod
    def delete_user_folder(self, user_id: int) -> StorageResponse:
        pass

    @abstractmethod
    def create_post_folder(self, post_id: int) -> StorageResponse:
        pass

    @abstractmethod
    def delete_post_folder(self, post_id: int) -> StorageResponse:
        pass
    
    @abstractmethod
    def upload_user_profile_image(self, user_id: int, image: UploadFile) -> StorageResponse:
        pass
    
    @abstractmethod
    def upload_user_cover_image(self, user_id: int, image: UploadFile) -> StorageResponse:
        pass

    @abstractmethod
    def upload_post_image(self, post_id: int, image: UploadFile) -> StorageResponse:
        pass

    @abstractmethod
    def delete_image(self, public_id: str) -> StorageResponse:
        pass
    

class CloudinaryStorage(Storage):

    def __init__(self):
        super().__init__()
    
    def open(self):
        cloudinary.config( 
            cloud_name = getenv("CLOUD_NAME"), 
            api_key = getenv("CLOUD_KEY"), 
            api_secret = getenv("CLOUD_SECRET"),
            secure=True
        )
    
    def close(self):
        return super().close()
    
    def create_user_folder(self, user_id) -> StorageResponse:
        try:
            r = cloudinary.api.create_folder(f"ougi_social/users/{user_id}")
            return StorageResponse(True, r)       
        except cloudinary.exceptions.Error as err:
            return StorageResponse(False, exception=err, err_msg="create_user_folder")
    
    def delete_user_folder(self, user_id) -> StorageResponse:
        try:
            r = cloudinary.api.delete_resources_by_prefix(f"ougi_social/users/{user_id}/")
            return StorageResponse(True, r)            
        except cloudinary.exceptions.Error as err:
            return StorageResponse(False, exception=err, err_msg="delete_user_folder")
    
    def create_post_folder(self, post_id: int) -> StorageResponse:
        try:
            r = cloudinary.api.create_folder(f"ougi_social/posts/{post_id}")
            return StorageResponse(True, r)            
        except cloudinary.exceptions.Error as err:
            return StorageResponse(False, exception=err, err_msg="create_post_folder")            

    def delete_post_folder(self, post_id: int) -> StorageResponse:
        try:
            r = cloudinary.api.delete_resources_by_prefix(f"ougi_social/posts/{post_id}")
            return StorageResponse(True, r)            
        except cloudinary.exceptions.Error as err:
            return StorageResponse(False, exception=err, err_msg="delete_post_folder")

    def upload_user_profile_image(self, user_id: int, image: UploadFile) -> StorageResponse:
        try:        
            r = cloudinary.uploader.upload(image.file, folder=f"ougi_social/users/{user_id}")            
            return StorageResponse(True, r)
        except Exception as err:
            return StorageResponse(False, exception=err, err_msg="upload_user_profile_image")            
    
    def upload_user_cover_image(self, user_id: int, image: UploadFile) -> StorageResponse:
        try:        
            r = cloudinary.uploader.upload(image.file, folder=f"ougi_social/users/{user_id}")
            return StorageResponse(True, r)
        except Exception as e:
            return StorageResponse(False, exception=e, err_msg="cloudinary_upload_user_cover_image")            
        
    def upload_post_image(self, post_id, image: UploadFile) -> StorageResponse:
        try:        
            r = cloudinary.uploader.upload(image.file, folder=f"ougi_social/posts/{post_id}")
            return StorageResponse(True, r)
        except Exception as e:
            return StorageResponse(False, exception=e, err_msg="cloudinary_upload_post_image")
    
    def delete_image(self, public_id: str) -> StorageResponse:
        try:
            r = cloudinary.uploader.destroy(public_id, resource_type="image")
            return StorageResponse(True, r)
        except Exception as e:
            return StorageResponse(False, exception=e, err_msg="cloudinary_delete_image")
    

storage = None


def create_storage(new_storage: Storage) -> None:
    global storage
    storage = new_storage


def get_storage() -> Storage:
    global storage
    return storage