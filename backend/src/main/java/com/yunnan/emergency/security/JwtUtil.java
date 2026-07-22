package com.yunnan.emergency.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.util.Date;

@Component
public class JwtUtil {

    private static final String SECRET =
            "yn-emergency-secret-key-2026-mvp-vertical-slice-very-long-strong-secret";
    private static final long EXPIRATION = 86400000L; // 24h

    private final SecretKey key = Keys.hmacShaKeyFor(SECRET.getBytes());

    public String generate(Long uid, String username, String roleKey, String realName) {
        return Jwts.builder()
                .setSubject(username)
                .claim("uid", uid)
                .claim("role", roleKey)
                .claim("name", realName)
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis() + EXPIRATION))
                .signWith(key)
                .compact();
    }

    public Claims parse(String token) {
        return Jwts.parserBuilder()
                .setSigningKey(key)
                .build()
                .parseClaimsJws(token)
                .getBody();
    }
}
