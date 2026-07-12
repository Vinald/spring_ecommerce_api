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
	@NotBlank
	private String name;
	@NotBlank
	private String description;
	@NotBlank
	private String category;
	@NotBlank
	private double price;
	@NotBlank
	private int quantity;

	private boolean available;
	private Date createdAt;
	private Date updatedAt;
}
