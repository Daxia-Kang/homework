"""账户系统测试用例。"""
import pytest
import tempfile
import os
from account.models import User, GameTypeRecord, Result
from account.hasher import PasswordHasher
from account.storage import AccountStorage
from account.service import AccountService


class TestPasswordHasher:
    """密码哈希测试。"""

    def test_hash_password(self):
        """测试密码哈希生成。"""
        password = "test123"
        hashed = PasswordHasher.hash_password(password)
        
        assert hashed.startswith("sha256:")
        assert len(hashed.split(":")) == 3

    def test_verify_password_correct(self):
        """测试正确密码验证。"""
        password = "test123"
        hashed = PasswordHasher.hash_password(password)
        
        assert PasswordHasher.verify_password(password, hashed)

    def test_verify_password_wrong(self):
        """测试错误密码验证。"""
        password = "test123"
        hashed = PasswordHasher.hash_password(password)
        
        assert not PasswordHasher.verify_password("wrong", hashed)

    def test_different_hashes(self):
        """测试相同密码生成不同哈希（因为盐值不同）。"""
        password = "test123"
        hash1 = PasswordHasher.hash_password(password)
        hash2 = PasswordHasher.hash_password(password)
        
        assert hash1 != hash2
        # 但两个都能验证
        assert PasswordHasher.verify_password(password, hash1)
        assert PasswordHasher.verify_password(password, hash2)


class TestAccountStorage:
    """账户存储测试。"""

    @pytest.fixture
    def temp_storage(self):
        """创建临时存储。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "users.json")
            yield AccountStorage(path)

    def test_save_and_load_user(self, temp_storage):
        """测试保存和加载用户。"""
        user = User(
            user_id="test_001",
            username="TestUser",
            password_hash="sha256:salt:hash",
            created_at="2025-01-01T00:00:00"
        )
        
        temp_storage.save_user(user)
        loaded = temp_storage.load_user("TestUser")
        
        assert loaded is not None
        assert loaded.user_id == user.user_id
        assert loaded.username == user.username

    def test_user_exists(self, temp_storage):
        """测试用户存在检查。"""
        assert not temp_storage.user_exists("TestUser")
        
        user = User(
            user_id="test_001",
            username="TestUser",
            password_hash="hash",
            created_at="2025-01-01"
        )
        temp_storage.save_user(user)
        
        assert temp_storage.user_exists("TestUser")
        assert temp_storage.user_exists("testuser")  # 不区分大小写


class TestAccountService:
    """账户服务测试。"""

    @pytest.fixture
    def service(self):
        """创建测试服务。"""
        AccountService.reset_instance()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "users.json")
            storage = AccountStorage(path)
            yield AccountService(storage)
            AccountService.reset_instance()

    def test_register_success(self, service):
        """测试注册成功。"""
        result = service.register("TestUser", "password123")
        
        assert result.is_success
        assert result.value.username == "TestUser"

    def test_register_duplicate(self, service):
        """测试重复注册。"""
        service.register("TestUser", "password123")
        result = service.register("TestUser", "password456")
        
        assert result.is_failure
        assert "已存在" in result.error

    def test_register_invalid_username(self, service):
        """测试无效用户名。"""
        result = service.register("ab", "password123")  # 太短
        assert result.is_failure

    def test_register_weak_password(self, service):
        """测试弱密码。"""
        result = service.register("TestUser", "12345")  # 太短
        assert result.is_failure

    def test_login_success(self, service):
        """测试登录成功。"""
        service.register("TestUser", "password123")
        result = service.login("TestUser", "password123")
        
        assert result.is_success
        assert service.get_current_user() is not None

    def test_login_wrong_password(self, service):
        """测试密码错误。"""
        service.register("TestUser", "password123")
        result = service.login("TestUser", "wrongpassword")
        
        assert result.is_failure
        assert "密码错误" in result.error

    def test_login_nonexistent_user(self, service):
        """测试用户不存在。"""
        result = service.login("NonExistent", "password")
        
        assert result.is_failure
        assert "不存在" in result.error

    def test_logout(self, service):
        """测试登出。"""
        service.register("TestUser", "password123")
        service.login("TestUser", "password123")
        
        assert service.is_logged_in()
        service.logout()
        assert not service.is_logged_in()

    def test_update_record(self, service):
        """测试更新战绩。"""
        service.register("TestUser", "password123")
        result = service.login("TestUser", "password123")
        user = result.value
        
        service.update_record(user.user_id, "othello", is_win=True)
        service.update_record(user.user_id, "othello", is_win=False)
        service.update_record(user.user_id, "othello", is_win=False, is_draw=True)
        
        # 重新加载用户
        updated = service._storage.load_user_by_id(user.user_id)
        record = updated.get_record("othello")
        
        assert record.total_games == 3
        assert record.wins == 1
        assert record.losses == 1
        assert record.draws == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
