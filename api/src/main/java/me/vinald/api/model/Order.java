package me.vinald.api.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.security.core.GrantedAuthority;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

@Data
@Entity
@Table(name = "user_orders")
@NoArgsConstructor
public class Order {
	@Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "user_id", nullable = false)
	private User user;

	@OneToMany(mappedBy = "order", cascade = CascadeType.ALL,fetch = FetchType.EAGER)
	private List<OrderItem> items = new ArrayList<>();

	@Enumerated(EnumType.STRING)
	private OrderStatus status;

	private double total;
	private LocalDateTime createdAt;

	@PrePersist
	protected  void onCreate(){
		this.createdAt = LocalDateTime.now();
		if (status == null) status = OrderStatus.PENDING;
	}

}
