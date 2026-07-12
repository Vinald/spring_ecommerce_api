package me.vinald.api.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import jakarta.validation.constraints.NotBlank;

import java.util.Date;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Entity
@Table(name = "products")
public class Product {
	@Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer productId;
	@NotBlank(message = "Product name is required")
	private String name;
	@NotBlank(message = "Product description is required")
	private String description;
	@NotBlank(message = "Product category is required")
	private String category;
	@NotBlank(message = "Product price is required")
	private double price;
	@NotBlank(message = "Product quantity is required and can not be negative")
	private int quantity;

	private boolean available;
	private Date createdAt;
	private Date updatedAt;
}
