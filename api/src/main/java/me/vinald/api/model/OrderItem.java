package me.vinald.api.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.aspectj.weaver.ast.Or;

@Entity
@Table(name = "order_items")
@Data
@NoArgsConstructor
public class OrderItem {
	@Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

	private Order order;
	private Product product;

	private int quantity;
	private double price;
}
