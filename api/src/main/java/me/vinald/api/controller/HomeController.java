package me.vinald.api.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HomeController {
	@GetMapping("/")
	public String home() {
		return "Welcome to the E-commerce application!";
	}

	@GetMapping("/about")
	public String about() {
		return "Ecommerce API - About";
	}
}
