from abc import ABC, abstractmethod
from fastapi import UploadFile
import cloudinary
import cloudinary.uploader
import cloudinary.api
import cloudinary.exceptions
from dotenv import load_dotenv
import os


load_dotenv()


class StorageResponse:
    
    def __init__(
            self, 
            content: dict[str, str] = {},
            success: bool = True, 
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
    def __init__(self, root_folder: str):
        self.__root_folder = root_folder
        if not self.__root_folder.endswith('/'):
            self.__root_folder += '/'
        self.open()

    @abstractmethod
    def open(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    def get_user_folder(self, user_id: int) -> str:
        return f"{self.__root_folder}users/{user_id}"
    
    def get_post_folder(self, post_id: int) -> str:
        return f"{self.__root_folder}posts/{post_id}"
    
    @abstractmethod
    def mkdir(self, dir: str) -> bool:
        pass

    @abstractmethod
    def rmdir(self, dir: str) -> bool:
        pass
    
    @abstractmethod
    def upload_image(self, image_folder: str, image: UploadFile) -> StorageResponse:
        pass

    @abstractmethod
    def delete_image(self, public_id: str) -> StorageResponse:
        pass
    

class CloudinaryStorage(Storage):

    def __init__(self):
        super().__init__()
    
    def open(self):
        cloudinary.config( 
            cloud_name = os.getenv("CLOUD_NAME"), 
            api_key = os.getenv("CLOUD_KEY"), 
            api_secret = os.getenv("CLOUD_SECRET"),
            secure=True
        )
    
    def close(self):
        return super().close()
    
    def mkdir(self, dir: str) -> StorageResponse:
        try:
            r = cloudinary.api.create_folder(dir)
            return StorageResponse(r)       
        except cloudinary.exceptions.Error as err:
            return StorageResponse(False, exception=err, err_msg=f"could not create {dir}")
    
    def rmdir(self, dir: str) -> StorageResponse:
        try:
            r = cloudinary.api.delete_resources_by_prefix(dir,)
            r1 = cloudinary.api.delete_folder(dir)
            return StorageResponse(r)
        except cloudinary.exceptions.Error as err:
            return StorageResponse(False, exception=err, err_msg="could not delete {dir}")        
    
    def upload_image(self, image_folder: str, image: UploadFile) -> StorageResponse:
        try:
            r = cloudinary.uploader.upload(image.file, folder=image_folder)
            return StorageResponse(r)
        except Exception as err:
            return StorageResponse(False, exception=err, err_msg="upload_user_profile_image")
    
    def delete_image(self, public_id: str) -> StorageResponse:
        try:
            r = cloudinary.uploader.destroy(public_id, resource_type="image")
            return StorageResponse(r)
        except Exception as e:
            return StorageResponse(False, exception=e, err_msg="cloudinary_delete_image")


storage = None


def create_storage(new_storage: Storage) -> None:
    global storage
    storage = new_storage


def get_storage() -> Storage:
    global storage
    return storage