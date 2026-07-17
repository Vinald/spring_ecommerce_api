package me.vinald.api.repository;

import me.vinald.api.model.Order;
import me.vinald.api.model.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface OrderRepository extends JpaRepository<Order, Long> {
	List<Order> findByUserOrderByCreatedAtDesc(User user);
}
