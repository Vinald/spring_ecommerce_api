package me.vinald.api.dto;

public record AuthResponse(
		String token,
		String refreshToken,
		String username,
		String role
) {
}
