import pygame 

#button class
class Button():
	def __init__(self,x, y, image, scale):
		width = image.get_width()
		height = image.get_height()
		self.original_image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
		self.image = self.original_image.copy()
		self.rect = self.image.get_rect()
		self.rect.topleft = (x, y)
		self.clicked = False
		
		# Hover effect parameters
		self.hover_scale = 1.1  # 10% size increase
		self.hover_brightness = 1.3  # 30% brightness increase
		self.is_hovering = False

	def draw(self, surface):
		action = False

		#get mouse position
		pos = pygame.mouse.get_pos()

		#check mouseover and clicked conditions
		if self.rect.collidepoint(pos):
			# Hover effect
			if not self.is_hovering:
				# Increase size
				new_width = int(self.rect.width * self.hover_scale)
				new_height = int(self.rect.height * self.hover_scale)
				self.image = pygame.transform.scale(self.original_image, (new_width, new_height))
				
				# Brighten the image
				bright_image = self.image.copy()
				bright_image.fill((255, 255, 255, 128), special_flags=pygame.BLEND_RGBA_MULT)
				self.image = bright_image
				
				# Adjust rect to center the enlarged button
				old_center = self.rect.center
				self.rect = self.image.get_rect()
				self.rect.center = old_center
				
				self.is_hovering = True

			if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
				action = True
				self.clicked = True

		else:
			# Reset to original state when not hovering
			if self.is_hovering:
				self.image = self.original_image.copy()
				old_center = self.rect.center
				self.rect = self.image.get_rect()
				self.rect.center = old_center
				self.is_hovering = False

		if pygame.mouse.get_pressed()[0] == 0:
			self.clicked = False

		#draw button
		surface.blit(self.image, (self.rect.x, self.rect.y))

		return action