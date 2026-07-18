package me.vinald.api.repository;

import me.vinald.api.model.RefreshToken;
import me.vinald.api.model.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface RefreshTokenRepository extends JpaRepository<RefreshToken, Long> {
	Optional<RefreshToken> findByToken(String token);
	void deleteByUser(User  user);
}
